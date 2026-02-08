import os
import traceback
import json
import io
import zipfile
import unicodedata
import re

from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Max, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.models import (
    A_Propos,
    Groupe_A_Propos,
    Image_A_Propos,
    Image_Service,
    Image_Site,
    Service,
    Site,
)
from apps.products.models import Famille, Image_Produit, Produit
from apps.reviews.models import Avis

from .admin_forms import (
    AProposForm,
    GroupeAProposForm,
    ImageServiceForm,
    ImageServiceFormSet,
    ImageSiteForm,
    ImageSlotForm,
    ServiceForm,
    SiteForm,
)


def _safe_basename(filename: str) -> str:
    """Retourne un nom de fichier 'basename' sûr (bloque tout chemin)."""
    name = os.path.basename(filename or "").strip()
    # bloquer toute tentative de path traversal ou nom vide
    if not name or name in {".", ".."}:
        raise ValueError("Nom de fichier invalide")
    if "/" in name or "\\" in name:
        raise ValueError("Nom de fichier invalide")
    return name


_IMAGE_CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/tiff": ".tif",
    "image/avif": ".avif",
    "image/svg+xml": ".svg",
}

_ALLOWED_IMAGE_EXTS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".svg",
    ".avif",
}


def _guess_image_extension(upload) -> str:
    """Devine une extension à partir du content-type / entête fichier.

    Retourne une string avec le point (ex: '.jpg') ou '' si inconnu.
    """
    content_type = (getattr(upload, "content_type", "") or "").lower().split(";")[0].strip()
    if content_type in _IMAGE_CONTENT_TYPE_TO_EXT:
        return _IMAGE_CONTENT_TYPE_TO_EXT[content_type]

    pos = None
    try:
        if hasattr(upload, "tell"):
            pos = upload.tell()
        if hasattr(upload, "seek"):
            upload.seek(0)
        img = PILImage.open(upload)
        fmt = (img.format or "").upper()
        img.close()
        fmt_to_ext = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "GIF": ".gif",
            "WEBP": ".webp",
            "BMP": ".bmp",
            "TIFF": ".tif",
        }
        return fmt_to_ext.get(fmt, "")
    except (UnidentifiedImageError, OSError, ValueError):
        return ""
    finally:
        try:
            if pos is not None and hasattr(upload, "seek"):
                upload.seek(pos)
        except Exception:
            pass


def _existing_site_image_filenames() -> set[str]:
    """Renvoie l'ensemble des noms (basename) déjà présents pour Image_Site (BD uniquement)."""
    existing = set(
        os.path.basename(img.image.name)
        for img in Image_Site.objects.exclude(image="")
    )
    return {name for name in existing if name}


_ZIP_IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
    ".svg",
}


def _zip_member_to_safe_filename(member_name: str) -> str | None:
    """Transforme un chemin de zip en un nom de fichier plat et sûr.

    - Ignore les dossiers et fichiers non-image.
    - Aplati l'arborescence: dossier/sous/img.png -> dossier_sous_img.png
    """
    if not member_name:
        return None
    normalized = str(member_name).replace("\\", "/")
    if normalized.endswith("/"):
        return None
    if normalized.startswith("__MACOSX/"):
        return None

    parts = [p for p in normalized.split("/") if p and p not in {".", ".."}]
    if not parts:
        return None

    leaf = parts[-1]
    _, ext = os.path.splitext(leaf)
    if ext.lower() not in _ZIP_IMAGE_EXTS:
        return None

    cleaned_parts: list[str] = []
    for p in parts:
        p = unicodedata.normalize("NFKC", str(p)).replace("\u00A0", " ")
        p = re.sub(r"\s+", "_", p.strip())
        if p:
            cleaned_parts.append(p)
    if not cleaned_parts:
        return None

    base_leaf, ext = os.path.splitext(cleaned_parts[-1])
    cleaned_parts[-1] = base_leaf or "image"

    filename = "_".join(cleaned_parts) + ext
    # sécurité: plus de séparateurs
    filename = filename.replace("/", "_").replace("\\", "_")

    # limiter la longueur (sur la plupart des FS: 255)
    if len(filename) > 240:
        base, ext = os.path.splitext(filename)
        base = base[: max(1, 240 - len(ext))]
        filename = f"{base}{ext}"

    return _safe_basename(filename)


def _extract_images_from_zip(zip_upload) -> list[SimpleUploadedFile]:
    """Extrait récursivement toutes les images d'un zip uploadé.

    Retourne une liste de SimpleUploadedFile (comme des fichiers envoyés via <input type=file>).
    """
    if not zip_upload:
        return []

    # bornes anti-zip-bomb raisonnables pour un import admin
    max_files = 500
    max_total_uncompressed = 200 * 1024 * 1024  # 200MB

    try:
        zip_bytes = zip_upload.read()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        raise ValueError("Impossible de lire le ZIP.") from exc

    extracted: list[SimpleUploadedFile] = []
    total_uncompressed = 0

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                safe_name = _zip_member_to_safe_filename(info.filename)
                if not safe_name:
                    continue

                total_uncompressed += int(getattr(info, "file_size", 0) or 0)
                if total_uncompressed > max_total_uncompressed:
                    raise ValueError("ZIP trop volumineux (taille décompressée).")

                extracted.append(SimpleUploadedFile(safe_name, zf.read(info)))
                if len(extracted) > max_files:
                    raise ValueError("ZIP contient trop d'images.")
    except zipfile.BadZipFile as exc:
        raise ValueError("Fichier ZIP invalide.") from exc

    return extracted


def _normalize_header(value: str) -> str:
    """Normalise une en-tête CSV (sans accents, lower, trim)."""
    value = (value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return value


def _parse_apropos_csv(file_bytes: bytes) -> list[dict]:
    """Parse un CSV A_Propos avec colonnes: Titre, Description, Photos.

    Supporte un champ Photos contenant des ';' non quotés en splittant uniquement
    les 2 premiers séparateurs du CSV (Titre/Description) puis en gardant le reste.
    """
    # Décodage souple (UTF-8 BOM / latin1 fallback)
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Encodage CSV non supporté")

    # Nettoyer les lignes vides
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    header_line = lines[0].strip()
    # Choix du séparateur principal: ';' ou ','
    delimiter = ";" if header_line.count(";") >= 2 else ","

    header_parts = [h.strip() for h in header_line.split(delimiter)]
    header_norm = [_normalize_header(h) for h in header_parts]

    # Indexer les colonnes attendues
    def _find_idx(*names: str) -> int | None:
        for name in names:
            norm = _normalize_header(name)
            if norm in header_norm:
                return header_norm.index(norm)
        return None

    idx_title = _find_idx("Titre", "Title")
    idx_desc = _find_idx("Description", "Desc")
    idx_photos = _find_idx("Photos", "Photo", "Images")

    if idx_title is None or idx_desc is None or idx_photos is None:
        raise ValueError("Colonnes CSV requises: Titre, Description, Photos")

    rows: list[dict] = []
    for raw in lines[1:]:
        # Split max 2 séparateurs pour conserver le champ Photos même s'il contient ';'
        parts = [p.strip() for p in raw.split(delimiter, 2)]
        if len(parts) < 3:
            # ligne invalide, on ignore
            continue

        # Reconstituer un tableau de 3 champs (Titre, Description, Photos)
        title = parts[0]
        desc = parts[1]
        photos_raw = parts[2].strip().strip('"').strip("'")

        # Parser les 3 positions: gauche;centre;droite
        photos = [p.strip() for p in photos_raw.split(";")]
        while len(photos) < 3:
            photos.append("")
        photos = photos[:3]

        if not title and not desc and not any(photos):
            continue

        rows.append({
            "titre": title,
            "description": desc,
            "photos": photos,
        })

    return rows

@login_required
def import_images_site_existing_names(request):
    """API: renvoie la liste des noms de fichiers déjà importés (basename)."""
    return JsonResponse({"names": sorted(_existing_site_image_filenames())})


@login_required
def import_images_site(request):
    """Importe plusieurs images du site en une fois, en conservant strictement les noms."""

    def _filename_no_spaces(name: str) -> bool:
        return not re.search(r"\s", (name or ""))

    def _wants_json() -> bool:
        accept = (request.headers.get("Accept") or "").lower()
        return request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in accept

    if request.method == "POST":
        image_files = request.FILES.getlist("images")
        zip_upload = request.FILES.get("zip_file")
        zip_files: list[SimpleUploadedFile] = []

        if zip_upload:
            try:
                zip_files = _extract_images_from_zip(zip_upload)
            except ValueError as exc:
                if _wants_json():
                    return JsonResponse(
                        {"ok": False, "error": str(exc), "conflicts": []},
                        status=400,
                    )
                messages.error(request, str(exc))
                return redirect("admin_core:admin_import_images_site")

        files = [*image_files, *zip_files]
        if not files:
            if _wants_json():
                return JsonResponse(
                    {"ok": False, "error": "Veuillez sélectionner au moins une image.", "conflicts": []},
                    status=400,
                )
            messages.error(request, "Veuillez sélectionner au moins une image.")
            return redirect("admin_core:admin_import_images_site")

        desired_names_raw = request.POST.get("desired_names", "")
        try:
            desired_names = json.loads(desired_names_raw) if desired_names_raw else None
        except json.JSONDecodeError:
            desired_names = None

        existing_names = _existing_site_image_filenames()

        # Construire les noms finaux à enregistrer (en gardant l'extension originale si besoin)
        final_names: list[str] = []
        conflicts: list[str] = []
        invalid_names: list[str] = []

        for idx, upload in enumerate(files):
            # Convention: pas d'espaces dans les noms (on remplace automatiquement à l'import)
            original_name = _safe_basename(upload.name)
            original_name = unicodedata.normalize("NFKC", str(original_name)).replace("\u00A0", " ")
            original_name = re.sub(r"\s+", "_", original_name)
            base, ext = os.path.splitext(original_name)
            if ext == "":
                ext = _guess_image_extension(upload)
                if ext:
                    original_name = f"{base}{ext}"

            wanted = None
            # `desired_names` ne s'applique qu'aux fichiers envoyés via le champ `images`.
            if idx < len(image_files) and isinstance(desired_names, list) and idx < len(desired_names):
                wanted = str(desired_names[idx] or "").replace("\u00A0", " ").strip()

            if wanted:
                wanted = _safe_basename(wanted)
                if not _filename_no_spaces(wanted):
                    invalid_names.append(wanted)
                    continue

                _wanted_base, wanted_ext = os.path.splitext(wanted)
                # Si l'utilisateur met un '.' dans le nom (ex: "photo.v1"),
                # on ne doit pas perdre l'extension d'origine.
                if wanted_ext == "" or wanted_ext.lower() not in _ALLOWED_IMAGE_EXTS:
                    filename = f"{wanted}{ext}" if ext else wanted
                else:
                    filename = wanted
            else:
                filename = original_name

            final_names.append(filename)

        if invalid_names:
            invalid_names = sorted(set(invalid_names))
            if _wants_json():
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Import bloqué: les noms ne doivent pas contenir d'espaces (utilisez des '_').",
                        "conflicts": invalid_names,
                    },
                    status=400,
                )
            messages.error(
                request,
                "Import annulé: les noms ne doivent pas contenir d'espaces (utilisez des '_'). "
                f"Conflits: {', '.join(invalid_names)}",
            )
            return redirect("admin_core:admin_import_images_site")

        # Détecter doublons dans le batch
        counts: dict[str, int] = {}
        for name in final_names:
            counts[name] = counts.get(name, 0) + 1
        duplicates_in_batch = {name for name, count in counts.items() if count > 1}
        conflicts.extend(sorted(duplicates_in_batch))

        # Détecter doublons avec l'existant (BD uniquement)
        media_dir = os.path.join(settings.MEDIA_ROOT, "images", "site")
        for name in final_names:
            if name in existing_names:
                conflicts.append(name)

        # Si conflit, refuser (le JS est censé gérer le popup, mais on sécurise côté serveur)
        if conflicts:
            conflicts = sorted(set(conflicts))
            if _wants_json():
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Conflit de noms de fichiers.",
                        "conflicts": conflicts,
                    },
                    status=409,
                )
            messages.error(
                request,
                "Import annulé: certains noms de fichiers existent déjà (ou sont dupliqués). "
                f"Conflits: {', '.join(conflicts)}",
            )
            return redirect("admin_core:admin_import_images_site")

        os.makedirs(media_dir, exist_ok=True)

        # Écriture stricte (pas de renommage automatique) + pas d'import partiel
        created = 0
        created_paths: list[str] = []
        created_ids: list[int] = []

        try:
            with transaction.atomic():
                for upload, filename in zip(files, final_names):
                    rel_path = os.path.join("images", "site", filename)
                    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

                    # On se base sur la BD comme source de vérité: si le fichier existe déjà sur disque
                    # mais qu'il n'est pas référencé en BD, on l'écrase (évite les faux conflits).
                    with open(abs_path, "wb") as f:
                        for chunk in upload.chunks():
                            f.write(chunk)
                    created_paths.append(abs_path)

                    img = Image_Site()
                    img.image.name = rel_path.replace(os.sep, "/")
                    img.save()
                    created_ids.append(img.pk)
                    created += 1
        except Exception:  # pylint: disable=broad-exception-caught
            for path in created_paths:
                try:
                    os.remove(path)
                except OSError:
                    pass
            Image_Site.objects.filter(pk__in=created_ids).delete()
            if _wants_json():
                return JsonResponse(
                    {
                        "ok": False,
                        "error": "Erreur inattendue pendant l'import.",
                        "conflicts": [],
                    },
                    status=500,
                )
            messages.error(request, "Import annulé: erreur inattendue pendant l'import.")
            return redirect("admin_core:admin_import_images_site")

        messages.success(request, f"{created} image(s) importée(s) avec succès.")
        if _wants_json():
            return JsonResponse(
                {"ok": True, "redirect": reverse("admin_core:admin_image_library")},
                status=200,
            )
        return redirect("admin_core:admin_image_library")

    return render(request, "admin/core/import_images_site.html")

def _process_service_images(request, service):
    """
    Traite les images d'un service via un inline formset.

    Traite les images du service indépendamment.
    Supprime toutes les images existantes et ajoute les nouvelles depuis POST.
    Les erreurs individuelles sont loggées sans bloquer le processus.
    """
    # IMPORTANT: le prefix du formset dépend du related_name du FK.
    # Ici on force un prefix stable, aligné avec le JS/AJAX (service_image_form).
    formset = ImageServiceFormSet(
        request.POST,
        request.FILES,
        instance=service,
        prefix="imageservice_set",
    )

    if not formset.is_valid():
        print(f"Formset invalid: {formset.errors}")
        return False

    # Laisser Django gérer ajouts/suppressions/modifs via le formset.
    # (évite de supprimer/recréer et surtout garantit la prise en compte des nouvelles cartes)
    try:
        formset.save()
    except Exception as exc:  # pylint: disable=broad-exception-caught
        print(f"Erreur lors de la sauvegarde du formset images service: {exc}")
        return False

    return True

@login_required
def admin_dashboard(request):
    """
    Affiche un tableau de bord admin avec statistiques des contenus.

    Vue pour la page d'accueil de l'administration
    Affiche un résumé des contenus et des liens vers les pages de gestion
    """

    # Récupération des statistiques pour affichage
    context = {
        # Core
        'nb_pages_apropos': A_Propos.objects.count(),
        'nb_services': Service.objects.count(),
        'nb_images_site': Image_Site.objects.count(),
        'site_config': Site.load(),

        # Products
        'nb_familles': Famille.objects.count(),
        'nb_produits': Produit.objects.count(),
        'nb_produits_du_moment': Produit.objects.filter(is_produit_du_moment=True).count(),

        # Reviews
        'nb_avis': Avis.objects.count(),
        'nb_avis_recents': Avis.objects.order_by('-date')[:5].count(),
    }

    return render(request, 'admin/dashboard.html', context)

@login_required
def edit_site(request):
    """Édite la configuration globale du site et permet l'ajout d'images dans la bibliothèque."""
    site = Site.load()
    color_defaults = {
        "page_foreground": Site._meta.get_field("page_foreground").default,
        "page_background": Site._meta.get_field("page_background").default,
        "card_background": Site._meta.get_field("card_background").default,
        "carousel_background": Site._meta.get_field("carousel_background").default,
        "border_primary": Site._meta.get_field("border_primary").default,
        "border_secondary": Site._meta.get_field("border_secondary").default,
        "text_title": Site._meta.get_field("text_title").default,
        "text_subtitle": Site._meta.get_field("text_subtitle").default,
        "text_normal": Site._meta.get_field("text_normal").default,
        "text_important": Site._meta.get_field("text_important").default,
        "text_discreet": Site._meta.get_field("text_discreet").default,
        "text_link": Site._meta.get_field("text_link").default,
        "text_header": Site._meta.get_field("text_header").default,
        "shadow": Site._meta.get_field("shadow").default,
        "button_color": Site._meta.get_field("button_color").default,
        "button_hover_color": Site._meta.get_field("button_hover_color").default,
    }

    if request.method == "POST":
        form = SiteForm(request.POST, request.FILES, instance=site)
        image_form = ImageSiteForm(request.POST, request.FILES)

        if "add_image" in request.POST and image_form.is_valid():
            image_form.save()
            messages.success(request, "Image ajoutée avec succès.")
            return redirect("admin_core:admin_site_edit")

        if "save_site" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Apparence du site mise à jour.")
            return redirect("admin_core:admin_site_edit")
    else:
        form = SiteForm(instance=site)
        image_form = ImageSiteForm()

    return render(request, "admin/core/site_edit.html", {
        "form": form,
        "image_form": image_form,
        "site": site,
        "color_defaults": color_defaults,
    })

EMPLACEMENT_AP = {
    "Gauche": "left",
    "Centre": "center",
    "Droite": "right",
}

@login_required
def apropos_list(request):
    """Liste les sections "À propos" groupées, triées par ordre d'affichage."""
    groups = (
        Groupe_A_Propos.objects
        .order_by("ordre_groupe", "pk")
        .prefetch_related(
            Prefetch(
                "sections",
                queryset=A_Propos.objects.order_by("ordre_ap", "pk"),
                to_attr="sections_ordered",
            )
        )
    )
    group_form = GroupeAProposForm()
    return render(
        request,
        "admin/core/apropos/apropos_list.html",
        {"groups": groups, "group_form": group_form},
    )


@login_required
@transaction.atomic
def apropos_group_add(request):
    """Crée un groupe "À propos" (ordre auto)."""
    if request.method != "POST":
        return redirect("admin_core:admin_apropos_list")

    form = GroupeAProposForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Veuillez corriger le nom du groupe.")
        return redirect("admin_core:admin_apropos_list")

    group = form.save(commit=False)
    max_ordre = Groupe_A_Propos.objects.aggregate(max_ordre=Max("ordre_groupe"))["max_ordre"] or 0
    group.ordre_groupe = max_ordre + 1
    try:
        group.save()
        messages.success(request, "Groupe « À propos » créé.")
    except Exception:  # pylint: disable=broad-exception-caught
        messages.error(request, "Impossible de créer ce groupe (nom/ordre déjà utilisé).")
    return redirect("admin_core:admin_apropos_list")


@login_required
@transaction.atomic
def apropos_group_move(request, pk, direction):
    """Change l'ordre d'un groupe "À propos" (up/down)."""
    group = get_object_or_404(Groupe_A_Propos, pk=pk)
    if direction == "up":
        swap = (
            Groupe_A_Propos.objects
            .filter(ordre_groupe__lt=group.ordre_groupe)
            .order_by("-ordre_groupe")
            .first()
        )
    else:  # down
        swap = (
            Groupe_A_Propos.objects
            .filter(ordre_groupe__gt=group.ordre_groupe)
            .order_by("ordre_groupe")
            .first()
        )

    if swap:
        old_a = group.ordre_groupe
        old_b = swap.ordre_groupe
        # Swap sûr avec contrainte unique (évite l'état intermédiaire invalide)
        tmp = (Groupe_A_Propos.objects.aggregate(max_ordre=Max("ordre_groupe"))["max_ordre"] or 0) + 1
        Groupe_A_Propos.objects.filter(pk=group.pk).update(ordre_groupe=tmp)
        Groupe_A_Propos.objects.filter(pk=swap.pk).update(ordre_groupe=old_a)
        Groupe_A_Propos.objects.filter(pk=group.pk).update(ordre_groupe=old_b)

    return redirect("admin_core:admin_apropos_list")


@login_required
def apropos_group_edit(request, pk):
    """Édite un groupe "À propos" (nom uniquement)."""
    group = get_object_or_404(Groupe_A_Propos, pk=pk)
    if request.method == "POST":
        form = GroupeAProposForm(request.POST, instance=group)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Groupe mis à jour.")
                return redirect("admin_core:admin_apropos_list")
            except Exception:  # pylint: disable=broad-exception-caught
                messages.error(request, "Impossible de modifier ce groupe (nom déjà utilisé).")
    else:
        form = GroupeAProposForm(instance=group)

    return render(
        request,
        "admin/core/apropos/groupe_edit.html",
        {"form": form, "group": group},
    )


@login_required
@transaction.atomic
def apropos_group_delete(request, pk):
    """Supprime un groupe "À propos" s'il est vide."""
    group = get_object_or_404(Groupe_A_Propos, pk=pk)

    if group.sections.exists():
        messages.warning(request, "Ce groupe contient des sections et ne peut pas être supprimé.")
        return redirect("admin_core:admin_apropos_list")

    try:
        deleted_order = group.ordre_groupe
        group.delete()
        Groupe_A_Propos.objects.filter(ordre_groupe__gt=deleted_order).update(
            ordre_groupe=models.F("ordre_groupe") - 1
        )
        messages.success(request, "Groupe supprimé.")
    except Exception:  # pylint: disable=broad-exception-caught
        messages.error(request, "Impossible de supprimer ce groupe.")

    return redirect("admin_core:admin_apropos_list")

@login_required
@transaction.atomic
def apropos_move(request, pk, direction):
    """Change l'ordre d'une section "À propos" en échangeant sa position avec la section voisine (up/down)."""
    page = get_object_or_404(A_Propos, pk=pk)

    if direction == "up":
        swap = (
            A_Propos.objects
            .filter(groupe=page.groupe, ordre_ap__lt=page.ordre_ap)
            .order_by("-ordre_ap")
            .first()
        )
    else:  # down
        swap = (
            A_Propos.objects
            .filter(groupe=page.groupe, ordre_ap__gt=page.ordre_ap)
            .order_by("ordre_ap")
            .first()
        )

    if swap:
        old_a = page.ordre_ap
        old_b = swap.ordre_ap
        # Swap sûr avec contrainte unique (groupe, ordre_ap)
        tmp = (
            A_Propos.objects.filter(groupe=page.groupe)
            .aggregate(max_ordre=Max("ordre_ap"))["max_ordre"]
            or 0
        ) + 1
        A_Propos.objects.filter(pk=page.pk).update(ordre_ap=tmp)
        A_Propos.objects.filter(pk=swap.pk).update(ordre_ap=old_a)
        A_Propos.objects.filter(pk=page.pk).update(ordre_ap=old_b)

    return redirect("admin_core:admin_apropos_list")

@login_required
def apropos_edit(request, pk=None):
    """Crée/modifie une section "À propos" et gère ses images par emplacement (gauche/centre/droite)."""
    page = get_object_or_404(A_Propos, pk=pk) if pk else None

    positions = ["Gauche", "Centre", "Droite"]
    existing = {p: None for p in positions}

    if page:
        for img in page.images.all():
            existing[img.position] = img

    if request.method == "POST":
        form = AProposForm(request.POST, instance=page)

        slot_forms = [
            (pos, ImageSlotForm(
                request.POST,
                request.FILES,
                prefix=pos,
                initial={"position": pos}
            ))
            for pos in positions
        ]

        valid = form.is_valid() and all(sf.is_valid() for pos, sf in slot_forms)

        if valid:
            page = form.save(commit=False)

            if page.pk is None:
                max_ordre = A_Propos.objects.filter(groupe=page.groupe).aggregate(
                    max_ordre=Max("ordre_ap")
                )["max_ordre"] or 0
                page.ordre_ap = max_ordre + 1
            page.save()
            for pos, sf in slot_forms:
                Image_A_Propos.objects.filter(page_ap=page, position=EMPLACEMENT_AP[pos]).delete()

                image = sf.cleaned_data["image"]
                upload = sf.cleaned_data["upload"]
                titre = sf.cleaned_data["titre_image"]

                if upload:
                    image = Image_Site.objects.create(image=upload)

                if image:
                    position = sf.cleaned_data["position"]
                    Image_A_Propos.objects.create(
                        page_ap=page,
                        image=image,
                        position=EMPLACEMENT_AP[position],
                        titre_image=titre,
                    )

            messages.success(request, "Section « À propos » enregistrée.")
            return redirect("admin_core:admin_apropos_list")
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        print("FORM PRINCIPAL ERRORS:", form.errors)

        for pos, sf in slot_forms:
            print(f"SLOT {pos} ERRORS:", sf.errors)
            print(f"SLOT {pos} NON FIELD ERRORS:", sf.non_field_errors())
            print(f"SLOT {pos} CLEANED:", getattr(sf, "cleaned_data", None))
    else:
        initial = {}
        if page is None:
            try:
                group_id = int(request.GET.get("groupe") or 0)
            except (TypeError, ValueError):
                group_id = 0
            if group_id:
                initial["groupe"] = group_id

        form = AProposForm(instance=page, initial=initial)
        slot_forms = [
            (
                pos,
                ImageSlotForm(
                    prefix=pos,
                    initial={
                        "position": pos,
                        "image": (
                            existing.get(EMPLACEMENT_AP[pos]).image
                            if existing.get(EMPLACEMENT_AP[pos])
                            else None
                        ),
                        "titre_image": (
                            existing.get(EMPLACEMENT_AP[pos]).titre_image
                            if existing.get(EMPLACEMENT_AP[pos])
                            else ""
                        ),
                    },
                ),
            )
            for pos in positions
        ]
    return render(request, "admin/core/apropos/apropos_edit.html", {
        "form": form,
        "slot_forms": slot_forms,
        "page": page,
    })

@login_required
def apropos_delete(request, pk):
    """Supprime une section "À propos" puis réajuste les ordres pour conserver une séquence 1..N."""
    page = get_object_or_404(A_Propos, pk=pk)
    deleted_order = page.ordre_ap
    group = page.groupe
    page.delete()

    # Réajuster les ordres pour garder 1..N
    A_Propos.objects.filter(
        groupe=group,
        ordre_ap__gt=deleted_order,
    ).update(ordre_ap=models.F("ordre_ap") - 1)

    messages.success(request, "Section « À propos » supprimée.")
    return redirect("admin_core:admin_apropos_list")

@login_required
def service_list(request):
    """Liste les services triés par ordre d'affichage."""
    services = Service.objects.order_by("ordre_service")
    return render(request, "admin/core/service/service_list.html", {
        "services": services
    })

@login_required
@transaction.atomic
def service_move(request, pk, direction):
    """Change l'ordre d'un service en échangeant sa position avec le service voisin (up/down)."""
    service = get_object_or_404(Service, pk=pk)

    if direction == "up":
        swap = (
            Service.objects
            .filter(ordre_service__lt=service.ordre_service)
            .order_by("-ordre_service")
            .first()
        )
    else:  # down
        swap = (
            Service.objects
            .filter(ordre_service__gt=service.ordre_service)
            .order_by("ordre_service")
            .first()
        )

    if swap:
        service.ordre_service, swap.ordre_service = (
            swap.ordre_service,
            service.ordre_service,
        )
        service.save()
        swap.save()

    return redirect("admin_core:admin_service_list")

@login_required
@transaction.atomic
def service_delete(request, pk):
    """Supprime un service puis réajuste l'ordre des services restants."""
    service = get_object_or_404(Service, pk=pk)
    deleted_order = service.ordre_service
    service.delete()

    Service.objects.filter(
        ordre_service__gt=deleted_order
    ).update(ordre_service=models.F("ordre_service") - 1)

    messages.success(request, "Service supprimé.")
    return redirect("admin_core:admin_service_list")

@login_required
@transaction.atomic
def service_add(request):
    """Crée un service (ordre auto) et gère l'ajout de ses images via formset."""
    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            max_order = Service.objects.aggregate(Max("ordre_service"))["ordre_service__max"] or 0
            service.ordre_service = max_order + 1
            service.save()

            # Traiter les images indépendamment
            if _process_service_images(request, service):
                messages.success(request, "Service ajouté.")
                return redirect("admin_core:admin_service_edit", pk=service.pk)
            messages.warning(request, "Service ajouté mais erreurs lors du traitement des images.")
            return redirect("admin_core:admin_service_edit", pk=service.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        formset = ImageServiceFormSet(request.POST, request.FILES, prefix="imageservice_set")
    else:
        form = ServiceForm()
        formset = ImageServiceFormSet(prefix="imageservice_set")

    template_form = ImageServiceForm(prefix="__prefix__")
    if 'DELETE' in template_form.fields:
        onchange = "if(this.checked) this.closest('.image-card').style.display='none';"
        template_form.fields['DELETE'].widget.attrs['onchange'] = onchange
    return render(request, "admin/core/service/service_edit.html", {
        "form": form,
        "formset": formset,
        "service": None,
        "template_form": template_form,
        "total_forms": formset.total_form_count(),
    })

@login_required
@transaction.atomic
def service_edit(request, pk):
    """Modifie un service existant et ses images associées via formset."""
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()

            # Traiter les images indépendamment
            if _process_service_images(request, service):
                messages.success(request, "Service enregistré.")
            else:
                messages.warning(request, "Service enregistré mais erreurs lors du traitement des images.")

            return redirect("admin_core:admin_service_edit", pk=service.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")

    form = ServiceForm(instance=service)
    formset = ImageServiceFormSet(instance=service, prefix="imageservice_set")

    template_form = ImageServiceForm(prefix="__prefix__")
    if 'DELETE' in template_form.fields:
        onchange = "if(this.checked) this.closest('.image-card').style.display='none';"
        template_form.fields['DELETE'].widget.attrs['onchange'] = onchange
    return render(request, "admin/core/service/service_edit.html", {
        "form": form,
        "formset": formset,
        "service": service,
        "template_form": template_form,
        "total_forms": formset.total_form_count(),
    })

@login_required
def upload_image(request):
    """Upload une image (site ou produit) et renvoie ses métadonnées en JSON pour l'UI admin."""
    image = request.FILES["image"]
    # Convention: éviter les espaces dans les noms de fichiers.
    # On remplace par '_' dès l'upload (UI + import CSV s'attendent à cette normalisation).
    try:
        name = os.path.basename(str(image.name))
        name = unicodedata.normalize("NFKC", name).replace("\u00A0", " ")
        image.name = re.sub(r"\s+", "_", name)
    except Exception:  # pylint: disable=broad-exception-caught
        pass
    image_type = request.POST.get("type", "site")
    product_id = request.POST.get("product_id", None)

    if image_type == "produit":
        if product_id is None or product_id == "":
            img = Image_Produit.objects.create(image=image)
        else:
            produit = Produit.objects.get(pk=product_id)
            img = Image_Produit.objects.create(image=image, produit=produit)
    else:
        img = Image_Site.objects.create(image=image)
    return JsonResponse({
        "image": {
            "id": img.id_image,
            "name": img.image.name,
            "url": img.image.url,
        }
    })

@login_required
def image_library(request):
    """Affiche la bibliothèque d'images du site avec pagination et liste des usages (logo/bandeau/à propos/services)."""
    images = Image_Site.objects.all().order_by("id_image")
    paginator = Paginator(images, 24)
    page_obj = paginator.get_page(request.GET.get("page"))

    image_data = []
    site = Site.load()

    for img in page_obj.object_list:
        usages = []
        # Check if used in Site
        if site.logo == img:
            usages.append({
                'text': "Logo du site",
                'url': reverse('admin_core:admin_site_edit')
            })
        if site.bandeau == img:
            usages.append({
                'text': "Bandeau du site",
                'url': reverse('admin_core:admin_site_edit')
            })
        # Check in A_Propos
        apropos_images = Image_A_Propos.objects.filter(image=img).select_related('page_ap')
        for ap_img in apropos_images:
            usages.append({
                'text': f"Page À propos: {ap_img.page_ap.titre_ap}",
                'url': reverse('admin_core:admin_apropos_edit', kwargs={'pk': ap_img.page_ap.pk})
            })
        # Check in Services
        service_images = Image_Service.objects.filter(image=img).select_related('service')
        for svc_img in service_images:
            usages.append({
                'text': f"Service: {svc_img.service.titre_service}",
                'url': reverse('admin_core:admin_service_edit', kwargs={'pk': svc_img.service.pk})
            })
        image_data.append({
            'image': img,
            'usages': usages,
            'is_used': len(usages) > 0
        })

    return render(request, "admin/core/image_library.html", {
        "image_data": image_data,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "current_sort_query": "",
        "current_querystring": "",
    })

@login_required
def image_delete(request, pk):
    """Supprime une image si elle n'est utilisée nulle part, sinon affiche un avertissement."""
    image = get_object_or_404(Image_Site, pk=pk)
    # Check if used
    is_used = (
        Site.objects.filter(logo=image).exists() or
        Site.objects.filter(bandeau=image).exists() or
        Image_A_Propos.objects.filter(image=image).exists() or
        Image_Service.objects.filter(image=image).exists()
    )
    if is_used:
        messages.warning(request, "L'image est utilisée et ne peut pas être supprimée.")
    else:
        image.delete()
        messages.success(request, "Image supprimée.")
    return redirect("admin_core:admin_image_library")


@login_required
def image_bulk_delete(request):
    """Supprime en masse des images (si non utilisées)."""
    if request.method != "POST":
        return redirect("admin_core:admin_image_library")

    if request.POST.get("select_all_unused") == "1":
        used_ids: set[int] = set()

        used_ids.update(
            Site.objects.exclude(logo__isnull=True).values_list("logo_id", flat=True)
        )
        used_ids.update(
            Site.objects.exclude(bandeau__isnull=True).values_list("bandeau_id", flat=True)
        )
        used_ids.update(Image_A_Propos.objects.values_list("image_id", flat=True))
        used_ids.update(Image_Service.objects.values_list("image_id", flat=True))

        qs = Image_Site.objects.all()
        if used_ids:
            qs = qs.exclude(pk__in=used_ids)

        deleted_count = qs.count()
        if deleted_count:
            qs.delete()
            messages.success(request, f"{deleted_count} image(s) supprimée(s).")
        return redirect("admin_core:admin_image_library")

    raw_ids = request.POST.getlist("selected_images")
    try:
        ids = [int(x) for x in raw_ids]
    except (TypeError, ValueError):
        messages.error(request, "Sélection invalide.")
        return redirect("admin_core:admin_image_library")

    if not ids:
        return redirect("admin_core:admin_image_library")

    images = Image_Site.objects.filter(pk__in=ids)

    deleted_count = 0
    skipped: list[str] = []
    for image in images:
        is_used = (
            Site.objects.filter(logo=image).exists() or
            Site.objects.filter(bandeau=image).exists() or
            Image_A_Propos.objects.filter(image=image).exists() or
            Image_Service.objects.filter(image=image).exists()
        )
        if is_used:
            skipped.append(str(image))
            continue

        image.delete()
        deleted_count += 1

    if deleted_count:
        messages.success(request, f"{deleted_count} image(s) supprimée(s).")
    if skipped:
        messages.warning(
            request,
            "Certaines images n'ont pas été supprimées car elles sont utilisées: "
            + ", ".join(skipped),
        )

    return redirect("admin_core:admin_image_library")

@login_required
def image_rename(request, pk):
    """Renomme physiquement le fichier sur disque puis met à jour le champ ImageField (MEDIA_ROOT)."""
    image = get_object_or_404(Image_Site, pk=pk)
    if request.method == "POST":
        new_name = request.POST.get('new_name')
        if new_name:
            # Rename the file
            old_path = os.path.join(settings.MEDIA_ROOT, image.image.name)
            dir_path = os.path.dirname(old_path)
            ext = os.path.splitext(image.image.name)[1]
            new_filename = new_name + ext
            new_path = os.path.join(dir_path, new_filename)
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
            # Update the field
            image.image.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
            image.save()
            messages.success(request, "Image renommée.")
        return redirect("admin_core:admin_image_library")
    current_name = os.path.splitext(os.path.basename(image.image.name))[0]
    return render(request, "admin/core/image_rename.html", {
        "image": image,
        "current_name": current_name,
    })

@login_required
def image_api(request):
    """API: renvoie une page d'images du site (id/nom/url) pour le sélecteur.

    Params GET:
    - page: int (1..)
    - page_size: int (optionnel)
    - q: str (optionnel) recherche par nom/path d'image
    """
    q = (request.GET.get("q") or "").strip()

    try:
        page = int(request.GET.get("page") or 1)
    except (TypeError, ValueError):
        page = 1
    page = max(page, 1)

    try:
        page_size = int(request.GET.get("page_size") or 60)
    except (TypeError, ValueError):
        page_size = 60
    page_size = max(1, min(page_size, 200))

    qs = Image_Site.objects.all()
    if q:
        # ImageField stocke un chemin (string) : on filtre dessus.
        qs = qs.filter(image__icontains=q)

    qs = qs.order_by("image")
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    image_data: list[dict] = []
    for img in page_obj.object_list:
        image_data.append({
            "id": img.id_image,
            "name": str(img),
            "url": img.image.url,
        })

    return JsonResponse(
        {
            "images": image_data,
            "pagination": {
                "page": page_obj.number,
                "page_size": page_size,
                "num_pages": paginator.num_pages,
                "count": paginator.count,
                "has_next": page_obj.has_next(),
                "has_previous": page_obj.has_previous(),
            },
        }
    )

@login_required
def service_image_form(request):
    """Retourne en JSON le HTML d'un formulaire (card) vide pour ajouter une image de service (AJAX)."""
    try:
        # Obtenir le prochain index depuis le request
        form_index = int(request.GET.get('index', 0))
        prefix = f'imageservice_set-{form_index}'

        form = ImageServiceForm(prefix=prefix)

        # Construire le HTML simplement sans f-strings complexes
        html = '<div class="image-card">'

        html += '<div class="image-card-toolbar">'
        html += '<button type="button" class="move-btn" onclick="moveImage(this, -1)" title="Déplacer à gauche">'
        html += '<span class="material-symbols-outlined">chevron_left</span>'
        html += '</button>'
        html += '<button type="button" class="move-btn" onclick="moveImage(this, 1)" title="Déplacer à droite">'
        html += '<span class="material-symbols-outlined">chevron_right</span>'
        html += '</button>'
        html += '<button type="button" class="delete-btn" onclick="removeImage(this)" title="Supprimer">'
        html += '<span class="material-symbols-outlined">close</span>'
        html += '</button>'
        html += '</div>'

        html += '<div class="form-group">'
        html += '<div class="image-selector-container">'
        html += '<div class="image-select-container">'
        html += '<button type="button" class="image-select-btn">'
        html += '<span class="material-symbols-outlined">image</span>'
        html += 'Sélectionner une image'
        html += '</button>'
        html += str(form['image'])
        html += '</div>'
        html += '<div class="image-preview-container" style="display: none; margin-top: 15px;">'
        html += '<div class="image-preview"></div>'
        html += '</div>'
        html += '</div>'
        html += '</div>'
        html += '<div class="form-group">'
        html += '<label class="form-label">Titre de l\'image</label>'
        html += str(form['titre_image'])
        html += '</div>'

        html += '<div class="form-group">'
        html += '<label class="form-label">Ordre</label>'
        html += str(form['ordre'])
        html += '</div>'

        html += '</div>'

        return JsonResponse({'html': html})
    except Exception as exc:  # pylint: disable=broad-exception-caught
        traceback.print_exc()
        return JsonResponse({'error': str(exc)}, status=500)

@login_required
def logout_view(request):
    """
    Déconnecte l'utilisateur de l'espace admin et affiche la page de logout.

    Vue pour la déconnexion de l'administration
    """
    logout(request)
    return render(request, 'admin/logout.html')
