import os
import io
import re
import traceback
import json
import csv
import unicodedata
import difflib
from urllib.parse import urlparse, unquote
from decimal import Decimal, InvalidOperation

from PIL import Image as PILImage
from PIL import UnidentifiedImageError

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .admin_forms import FamilleForm, ImageProduitForm, ImageProduitFormSet, ProduitForm
from .models import Famille, Image_Produit, Produit


def _normalize_header(value: str) -> str:
    value = (value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return value


def _normalize_family_key(value: str) -> str:
    value = (value or "").strip().lower()
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = " ".join(value.split())
    return value


def _parse_bool(value: str) -> bool:
    v = (value or "").strip().lower()
    return v in {"y", "yes", "o", "oui"}


def _parse_int(value: str) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _normalize_image_ref(value: str) -> str:
    """Normalise une référence d'image venant du CSV.

    - accepte un nom de fichier ou une URL
    - decode %XX
    - remplace les espaces par '_' (convention des imports)
    - garde uniquement le basename (pas de chemin)
    """
    raw = str(value or "")
    raw = raw.replace("\u00A0", " ")  # NBSP
    raw = raw.strip()
    if not raw:
        return ""

    # Si c'est une URL, garder uniquement le path.
    parsed = urlparse(raw)
    if parsed.scheme and parsed.netloc:
        raw = parsed.path

    raw = unquote(raw)
    raw = unicodedata.normalize("NFKC", raw)
    # Convention import: remplacer tout whitespace par '_'
    raw = re.sub(r"\s+", "_", raw)
    return _safe_basename(raw)


def _clean_cell_text(value: str) -> str:
    v = str(value or "")
    v = v.replace("\u00A0", " ")  # NBSP
    return v.strip()


def _parse_produits_csv(file_bytes: bytes) -> list[dict]:
    """Parse un CSV Produits.

    Formats supportés:
    - Nouveau format (tableur-friendly):
      Nom,Prix,Famille,Description,ProduitDuMoment,PhotoDuMoment,<photo1>,<photo2>,...
      (les colonnes photo peuvent avoir un header vide; tout ce qui est après PhotoDuMoment est traité comme photo)

    - Ancien format (compat): colonne "Photos" contenant une liste séparée par ';'

    Notes:
    - Délimiteur de colonnes: ',' ou ';' (auto-détecté)
    - Champs quotés supportés (y compris avec retours à la ligne)
    - Description: supporte les "\\n" littéraux (convertis en vrais retours à la ligne)
    """
    text = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise ValueError("Encodage CSV non supporté")

    if not text.strip():
        return []

    # Détecter le délimiteur (',' ou ';') sans casser les champs multi-lignes
    sample = text[:4096]
    delimiter = ","
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;")
        delimiter = dialect.delimiter
    except Exception:  # pylint: disable=broad-exception-caught
        # fallback simple: compter sur la première ligne non vide
        first = next((ln for ln in text.splitlines() if ln.strip()), "")
        if first.count(";") > first.count(","):
            delimiter = ";"

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    try:
        header = next(reader)
    except StopIteration:
        return []

    header_norm = [_normalize_header(h) for h in header]

    def index_of(name: str) -> int | None:
        return header_norm.index(name) if name in header_norm else None

    idx_nom = index_of("nom")
    idx_prix = index_of("prix")
    idx_famille = index_of("famille")
    idx_description = index_of("description")
    idx_pdm = index_of("produitdumoment")
    idx_pdm_photo = index_of("photodumoment")
    idx_photos = index_of("photos")

    # Déterminer le format
    has_old_photos_col = idx_photos is not None
    has_new_6_cols = all(i is not None for i in (idx_nom, idx_prix, idx_famille, idx_description, idx_pdm, idx_pdm_photo))

    # Fallback: si les 6 premières colonnes sont dans l'ordre attendu (Nom..PhotoDuMoment)
    if not has_old_photos_col and not has_new_6_cols:
        expected = ["nom", "prix", "famille", "description", "produitdumoment", "photodumoment"]
        if header_norm[:6] == expected:
            idx_nom, idx_prix, idx_famille, idx_description, idx_pdm, idx_pdm_photo = range(6)
            has_new_6_cols = True

    if not has_old_photos_col and not has_new_6_cols:
        raise ValueError(
            "CSV invalide: colonnes attendues: Nom,Prix,Famille,Description,ProduitDuMoment,PhotoDuMoment puis des colonnes photos"
        )

    rows: list[dict] = []

    for row in reader:
        if not row or all(not _clean_cell_text(c) for c in row):
            continue

        def get_i(i: int | None) -> str:
            if i is None:
                return ""
            return _clean_cell_text(row[i] if i < len(row) else "")

        warnings: list[str] = []

        nom = get_i(idx_nom)
        prix_raw = get_i(idx_prix)
        famille = get_i(idx_famille)
        description = get_i(idx_description)

        # Description: supporter les "\\n" littéraux
        if "\\n" in description:
            description = description.replace("\\n", "\n")

        # Produit du moment: seulement o/O/y/oui => True, sinon False (warning si valeur inconnue)
        pdm_raw = get_i(idx_pdm)
        v = (pdm_raw or "").strip().lower()
        produit_du_moment = v in {"o", "oui", "y"}
        if v and not produit_du_moment and v not in {"n", "non", "no", "0", "false"}:
            warnings.append(f"ProduitDuMoment '{pdm_raw}' interprété comme NON")

        # Photos
        photos: list[str] = []
        if has_old_photos_col:
            photos_raw = get_i(idx_photos)
            if photos_raw:
                for p in photos_raw.split(";"):
                    before = _clean_cell_text(p)
                    if not before:
                        continue
                    after = _normalize_image_ref(before)
                    if before != after:
                        warnings.append(f"Photo nettoyée: '{before}' → '{after}'")
                    photos.append(after)
        else:
            last_fixed_idx = max(i for i in (idx_nom, idx_prix, idx_famille, idx_description, idx_pdm, idx_pdm_photo) if i is not None)
            for cell in row[last_fixed_idx + 1:]:
                before = _clean_cell_text(cell)
                if not before:
                    continue
                after = _normalize_image_ref(before)
                if before != after:
                    warnings.append(f"Photo nettoyée: '{before}' → '{after}'")
                photos.append(after)

        # Photo du moment (1-based)
        photo_du_moment = _parse_int(get_i(idx_pdm_photo))
        if photos:
            if photo_du_moment is None:
                warnings.append("PhotoDuMoment manquant: mis à 1")
                photo_du_moment = 1
            if photo_du_moment < 1 or photo_du_moment > len(photos):
                warnings.append(
                    f"PhotoDuMoment '{get_i(idx_pdm_photo)}' invalide (1..{len(photos)}): mis à 1"
                )
                photo_du_moment = 1
        else:
            # pas de photos => ignorer l'index
            if photo_du_moment is not None:
                warnings.append("PhotoDuMoment ignoré: aucune photo")
            photo_du_moment = None

        rows.append({
            "famille": famille,
            "nom": nom,
            "photos": photos,
            "description": description,
            "prix": prix_raw,
            "produit_du_moment": produit_du_moment,
            "photo_du_moment": photo_du_moment,
            "warnings": warnings,
        })

    return rows


def _build_family_groups(rows: list[dict]) -> list[dict]:
    groups: dict[str, dict] = {}
    for r in rows:
        fam = (r.get("famille") or "").strip()
        key = _normalize_family_key(fam)
        if not key:
            continue
        if key not in groups:
            groups[key] = {
                "key": key,
                "default": fam,
                "variants": [],
            }
        if fam and fam not in groups[key]["variants"]:
            groups[key]["variants"].append(fam)
    return list(groups.values())


def _build_family_merge_suggestions(family_groups: list[dict]) -> list[dict]:
    # Suggestions "douces" pour aider à fusionner (Aimants vs Aiments)
    suggestions: list[dict] = []
    names = [(g["key"], g.get("default") or g["key"]) for g in family_groups]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            k1, n1 = names[i]
            k2, n2 = names[j]
            ratio = difflib.SequenceMatcher(None, _normalize_family_key(n1), _normalize_family_key(n2)).ratio()
            if ratio >= 0.84 and k1 != k2:
                suggestions.append({"from": k1, "to": k2, "ratio": round(ratio, 2), "a": n1, "b": n2})
    return suggestions


def _parse_price(value: str) -> Decimal | None:
    raw = _clean_cell_text(value)
    if not raw:
        return None

    raw = raw.replace("€", "")
    raw = raw.replace("EUR", "").replace("eur", "")
    raw = raw.strip()

    # Gérer séparateurs ',' et '.' (décimal vs milliers)
    last_comma = raw.rfind(",")
    last_dot = raw.rfind(".")
    if last_comma != -1 and last_dot != -1:
        # Le séparateur le plus à droite est le décimal
        if last_comma > last_dot:
            raw = raw.replace(".", "")
            raw = raw.replace(",", ".")
        else:
            raw = raw.replace(",", "")
    else:
        # un seul type de séparateur, tolérer la virgule décimale
        raw = raw.replace(",", ".")

    # Retirer tout ce qui n'est pas chiffre/point/signe
    raw = re.sub(r"[^0-9.\-]", "", raw)
    if raw in {"", ".", "-", "-."}:
        return None

    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


@login_required
def import_produits(request):
    """Import CSV des produits avec édition et validation bloquante des images."""
    if request.method == "POST":
        step = request.POST.get("step", "parse")

        if step == "parse":
            csv_file = request.FILES.get("csv_file")
            if not csv_file:
                messages.error(request, "Veuillez sélectionner un fichier CSV.")
                return redirect("admin_produits:admin_import_produits")

            try:
                rows = _parse_produits_csv(csv_file.read())
            except Exception as exc:  # pylint: disable=broad-exception-caught
                messages.error(request, f"CSV invalide: {exc}")
                return redirect("admin_produits:admin_import_produits")

            if not rows:
                messages.warning(request, "Aucune ligne importable n'a été trouvée.")
                return redirect("admin_produits:admin_import_produits")

            # Index images produits par nom exact (basename)
            images = Image_Produit.objects.all()
            by_name = {os.path.basename(img.image.name): img for img in images if img.image.name}

            # Familles
            family_groups = _build_family_groups(rows)
            existing_families = Famille.objects.values_list("nom_famille", flat=True)
            existing_keys = {_normalize_family_key(n) for n in existing_families}
            for g in family_groups:
                g["exists"] = g["key"] in existing_keys

            suggestions = _build_family_merge_suggestions(family_groups)

            resolved_rows = []
            missing_images = 0
            missing_familles = 0
            warnings_total = 0

            for r in rows:
                fam_name = (r.get("famille") or "").strip()
                fam_key = _normalize_family_key(fam_name)
                if fam_key and fam_key not in existing_keys:
                    missing_familles += 1

                photo_cells = []
                photos = r.get("photos") or []
                pdm = r.get("photo_du_moment")

                row_warnings = list(r.get("warnings") or [])
                warnings_total += len(row_warnings)

                for name in photos:
                    filename = os.path.basename(name)
                    img = by_name.get(filename)
                    if filename and img is None:
                        missing_images += 1
                    photo_cells.append({
                        "requested": filename,
                        "image": (
                            {
                                "id": img.id_image,
                                "name": img.image.url.split('/')[-1],
                                "url": img.image.url,
                            }
                            if img else None
                        ),
                    })

                resolved_rows.append({
                    "famille": fam_name,
                    "famille_key": fam_key,
                    "nom": (r.get("nom") or "").strip(),
                    "description": (r.get("description") or "").strip(),
                    "prix": (r.get("prix") or "").strip(),
                    "produit_du_moment": bool(r.get("produit_du_moment")),
                    "photo_du_moment": pdm,
                    "photos": photo_cells,
                    "warnings": row_warnings,
                })

            return render(request, "admin/products/import_produits.html", {
                "step": "resolve",
                "rows": resolved_rows,
                "rows_json": json.dumps(rows, ensure_ascii=False),
                "family_groups": family_groups,
                "merge_suggestions": suggestions,
                "missing_images": missing_images,
                "missing_familles": missing_familles,
                "warnings_total": warnings_total,
            })

        if step == "import":
            rows_json = request.POST.get("rows_json", "")
            try:
                rows = json.loads(rows_json) if rows_json else []
            except json.JSONDecodeError:
                rows = []

            if not isinstance(rows, list) or not rows:
                messages.error(request, "Import impossible: données manquantes. Veuillez relancer l'import.")
                return redirect("admin_produits:admin_import_produits")

            # Familles: récupérer config (nom final + fusions)
            initial_groups = _build_family_groups(rows)
            group_keys = [g["key"] for g in initial_groups]

            # Ajouts manuels côté UI
            added_raw = request.POST.get("added_families_json", "[]")
            try:
                added = json.loads(added_raw) if added_raw else []
            except json.JSONDecodeError:
                added = []
            if isinstance(added, list):
                for name in added:
                    name = (str(name or "")).strip()
                    if not name:
                        continue
                    key = _normalize_family_key(name)
                    if key and key not in group_keys:
                        initial_groups.append({"key": key, "default": name, "variants": [name]})
                        group_keys.append(key)

            final_name_by_key: dict[str, str] = {}
            merge_into: dict[str, str] = {}
            for g in initial_groups:
                key = g["key"]
                final_name = (request.POST.get(f"family-{key}-final") or g.get("default") or "").strip()
                final_name_by_key[key] = final_name or g.get("default") or key
                target = (request.POST.get(f"family-{key}-merge_into") or "").strip()
                if target and target in group_keys and target != key:
                    merge_into[key] = target

            def resolve_family_key(key: str) -> str:
                seen: set[str] = set()
                cur = key
                while cur in merge_into and cur not in seen:
                    seen.add(cur)
                    cur = merge_into[cur]
                return cur

            # Construire les lignes affichées (avec corrections utilisateur)
            by_name = {
                os.path.basename(img.image.name): img
                for img in Image_Produit.objects.exclude(image="")
                if img.image.name
            }

            display_rows = []
            missing_images = 0
            validation_errors: list[str] = []
            warnings_total = 0

            for idx, r in enumerate(rows):
                row_warnings = list(r.get("warnings") or [])

                nom = (request.POST.get(f"rows-{idx}-nom") or r.get("nom") or "").strip()
                description = (request.POST.get(f"rows-{idx}-description") or r.get("description") or "").strip()
                prix_raw = (request.POST.get(f"rows-{idx}-prix") or r.get("prix") or "").strip()
                prix_value = _parse_price(prix_raw)
                if prix_raw and prix_value is None:
                    row_warnings.append(f"Prix '{prix_raw}' invalide: ignoré")

                fam_key_post = (request.POST.get(f"rows-{idx}-famille_key") or "").strip()
                fam_key = fam_key_post or _normalize_family_key(r.get("famille") or "")
                fam_key = resolve_family_key(fam_key) if fam_key else fam_key

                if not nom:
                    validation_errors.append(f"Ligne {idx+1}: nom manquant")
                if not fam_key:
                    validation_errors.append(f"Ligne {idx+1}: famille manquante")

                produit_du_moment = request.POST.get(f"rows-{idx}-produit_du_moment") == "on"

                photos = r.get("photos") or []
                photo_cells = []
                for photo_i, name in enumerate(photos):
                    filename = os.path.basename(str(name or ""))
                    field = f"rows-{idx}-photo-{photo_i}-image_existing"
                    image_id = (request.POST.get(field) or "").strip()

                    img = None
                    if image_id:
                        try:
                            img_obj = Image_Produit.objects.get(pk=int(image_id))
                            img = {
                                "id": img_obj.id_image,
                                "name": img_obj.image.url.split('/')[-1],
                                "url": img_obj.image.url,
                            }
                        except Exception:  # pylint: disable=broad-exception-caught
                            img = None

                    # Si pas sélectionné, tenter auto-match (au cas où)
                    if not img and filename:
                        auto = by_name.get(filename)
                        if auto:
                            img = {
                                "id": auto.id_image,
                                "name": auto.image.url.split('/')[-1],
                                "url": auto.image.url,
                            }
                            image_id = str(auto.id_image)

                    if filename and not image_id:
                        missing_images += 1
                        validation_errors.append(f"Ligne {idx+1}: image introuvable '{filename}'")

                    photo_cells.append({
                        "requested": filename,
                        "image": img,
                        "selected_id": image_id,
                    })

                # Photo du moment
                # Si le champ est présent dans le POST (même vide), on respecte la saisie utilisateur
                # (permet de "vider" la valeur) au lieu de retomber sur la valeur CSV.
                pdm_raw = request.POST.get(f"rows-{idx}-photo_du_moment", None)
                pdm = _parse_int(pdm_raw) if pdm_raw is not None else _parse_int(r.get("photo_du_moment"))
                if photos:
                    if pdm is None:
                        row_warnings.append("PhotoDuMoment manquant: mis à 1")
                        pdm = 1
                    if pdm < 1 or pdm > len(photos):
                        row_warnings.append(f"PhotoDuMoment '{pdm_raw or r.get('photo_du_moment')}' invalide (1..{len(photos)}): mis à 1")
                        pdm = 1
                else:
                    if pdm is not None:
                        row_warnings.append("PhotoDuMoment ignoré: aucune photo")
                    pdm = None

                warnings_total += len(row_warnings)

                display_rows.append({
                    "famille": final_name_by_key.get(fam_key, r.get("famille") or ""),
                    "famille_key": fam_key,
                    "nom": nom,
                    "description": description,
                    "prix": prix_raw,
                    "produit_du_moment": produit_du_moment,
                    "photo_du_moment": pdm,
                    "photos": photo_cells,
                    "warnings": row_warnings,
                })

            if validation_errors:
                messages.error(request, "Validation bloquée: corrigez les champs en erreur (images/nom/famille).")
                return render(request, "admin/products/import_produits.html", {
                    "step": "resolve",
                    "rows": display_rows,
                    "rows_json": rows_json,
                    "family_groups": [
                        {
                            "key": k,
                            "default": final_name_by_key.get(k, k),
                            "variants": [],
                            "exists": Famille.objects.filter(nom_famille__iexact=final_name_by_key.get(k, k)).exists(),
                        }
                        for k in group_keys
                    ],
                    "merge_suggestions": [],
                    "missing_images": missing_images,
                    "missing_familles": 0,
                    "validation_errors": validation_errors,
                    "added_families_json": added_raw,
                    "warnings_total": warnings_total,
                })

            created = 0
            with transaction.atomic():
                # Créer/récupérer familles (1 seule par nom final)
                famille_cache: dict[str, Famille] = {}
                for idx, row in enumerate(display_rows):
                    fam_name = (row.get("famille") or "").strip()
                    if not fam_name:
                        messages.error(request, f"Ligne {idx+1}: famille manquante")
                        raise ValueError("Famille manquante")
                    if fam_name not in famille_cache:
                        famille_cache[fam_name], _ = Famille.objects.get_or_create(nom_famille=fam_name)

                # Créer produits + associer images
                for row in display_rows:
                    famille = famille_cache[(row.get("famille") or "").strip()]
                    prix_value = _parse_price(row.get("prix") or "")
                    produit = Produit.objects.create(
                        famille=famille,
                        nom_produit=row.get("nom") or "",
                        description_produit=row.get("description") or "",
                        prix_produit=prix_value,
                        is_produit_du_moment=bool(row.get("produit_du_moment")),
                    )

                    # Lier images (ordre = ordre CSV)
                    selected_ids: list[int] = []
                    for i, photo in enumerate(row.get("photos") or []):
                        sid = str(photo.get("selected_id") or "").strip()
                        if not sid:
                            continue
                        try:
                            selected_ids.append(int(sid))
                        except ValueError:
                            continue

                        img_obj = Image_Produit.objects.get(pk=int(sid))
                        img_obj.produit = produit
                        img_obj.ordre = i + 1
                        img_obj.is_image_du_moment = False
                        img_obj.save(update_fields=["produit", "ordre", "is_image_du_moment"])

                    # Image du moment (1-based)
                    pdm = row.get("photo_du_moment")
                    if pdm and isinstance(pdm, int) and 1 <= pdm <= len(selected_ids):
                        chosen_id = selected_ids[pdm - 1]
                        Image_Produit.objects.filter(produit=produit).update(is_image_du_moment=False)
                        Image_Produit.objects.filter(pk=chosen_id, produit=produit).update(is_image_du_moment=True)

                    created += 1

            messages.success(request, f"{created} produit(s) importé(s).")
            return redirect("admin_produits:admin_produit_list")

    return render(request, "admin/products/import_produits.html", {"step": "upload"})

def _safe_basename(filename: str) -> str:
    """Retourne un nom de fichier 'basename' sûr (bloque tout chemin)."""
    name = os.path.basename(filename or "").strip()
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

    # Fallback: essayer via Pillow (lecture des en-têtes). On restaure le curseur ensuite.
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


def _existing_product_image_filenames() -> set[str]:
    """Renvoie l'ensemble des noms (basename) déjà présents pour Image_Produit (BD uniquement)."""
    existing = set(
        os.path.basename(img.image.name)
        for img in Image_Produit.objects.exclude(image="")
    )
    return {name for name in existing if name}

@login_required
def import_images_produits_existing_names(request):
    """API: renvoie la liste des noms de fichiers déjà importés (basename) pour les images produits."""
    return JsonResponse({"names": sorted(_existing_product_image_filenames())})


@login_required
def import_images_produits(request):
    """Importe plusieurs images produits en une fois, en conservant strictement les noms."""

    def _filename_no_spaces(name: str) -> bool:
        return not re.search(r"\s", (name or ""))

    def _wants_json() -> bool:
        accept = (request.headers.get("Accept") or "").lower()
        return request.headers.get("X-Requested-With") == "XMLHttpRequest" or "application/json" in accept

    if request.method == "POST":
        files = request.FILES.getlist("images")
        if not files:
            if _wants_json():
                return JsonResponse(
                    {"ok": False, "error": "Veuillez sélectionner au moins une image.", "conflicts": []},
                    status=400,
                )
            messages.error(request, "Veuillez sélectionner au moins une image.")
            return redirect("admin_produits:admin_import_images_produits")

        desired_names_raw = request.POST.get("desired_names", "")
        try:
            desired_names = json.loads(desired_names_raw) if desired_names_raw else None
        except json.JSONDecodeError:
            desired_names = None

        existing_names = _existing_product_image_filenames()

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
            if isinstance(desired_names, list) and idx < len(desired_names):
                wanted = str(desired_names[idx] or "").strip()

            if wanted:
                wanted = _safe_basename(wanted)
                if not _filename_no_spaces(wanted):
                    invalid_names.append(wanted)
                    continue
                wanted_base, wanted_ext = os.path.splitext(wanted)
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
            return redirect("admin_produits:admin_import_images_produits")

        # doublons dans le batch
        counts: dict[str, int] = {}
        for name in final_names:
            counts[name] = counts.get(name, 0) + 1
        duplicates_in_batch = {name for name, count in counts.items() if count > 1}
        conflicts.extend(sorted(duplicates_in_batch))

        # doublons avec l'existant (BD uniquement)
        media_dir = os.path.join(settings.MEDIA_ROOT, "images", "produits")
        for name in final_names:
            if name in existing_names:
                conflicts.append(name)

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
            return redirect("admin_produits:admin_import_images_produits")

        os.makedirs(media_dir, exist_ok=True)

        created = 0
        created_paths: list[str] = []
        created_ids: list[int] = []

        try:
            with transaction.atomic():
                for upload, filename in zip(files, final_names):
                    rel_path = os.path.join("images", "produits", filename)
                    abs_path = os.path.join(settings.MEDIA_ROOT, rel_path)

                    # On se base sur la BD comme source de vérité: si le fichier existe déjà sur disque
                    # mais qu'il n'est pas référencé en BD, on l'écrase (évite les faux conflits).
                    with open(abs_path, "wb") as f:
                        for chunk in upload.chunks():
                            f.write(chunk)
                    created_paths.append(abs_path)

                    img = Image_Produit()
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
            Image_Produit.objects.filter(pk__in=created_ids).delete()
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
            return redirect("admin_produits:admin_import_images_produits")

        messages.success(request, f"{created} image(s) importée(s) avec succès.")
        if _wants_json():
            return JsonResponse(
                {"ok": True, "redirect": reverse("admin_produits:admin_produit_image_library")},
                status=200,
            )
        return redirect("admin_produits:admin_produit_image_library")

    return render(request, "admin/products/import_images_produits.html")

@login_required
def image_produit_api(request):
    """API: renvoie une page d'images produit (id/nom/url) pour le sélecteur.

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

    qs = Image_Produit.objects.all()
    if q:
        qs = qs.filter(image__icontains=q)

    qs = qs.order_by("image")
    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    image_data: list[dict] = []
    for img in page_obj.object_list:
        image_data.append(
            {
                "id": img.id_image,
                "name": img.image.url.split("/")[-1],
                "url": img.image.url,
            }
        )

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
def famille_list(request):
    """Liste les familles avec annotation du nombre de produits associés."""
    familles = (
        Famille.objects
        .annotate(nb_produits=Count("famille"))  # related_name="famille" sur Produit.famille
        .order_by("nom_famille")
    )

    return render(request, "admin/products/familles/famille_list.html", {
        "familles": familles
    })


@login_required
def famille_delete(request, pk):
    """Supprime une famille si aucun produit ne l'utilise (sinon avertit)."""
    famille = get_object_or_404(Famille, pk=pk)

    if famille.famille.exists():  # related_name="famille" sur Produit.famille
        messages.warning(request, "Impossible de supprimer : des produits utilisent cette famille.")
        return redirect("admin_produits:admin_famille_list")

    famille.delete()
    messages.success(request, "Famille supprimée.")
    return redirect("admin_produits:admin_famille_list")

@login_required
def famille_add(request):
    """Crée une nouvelle famille via FamilleForm."""
    if request.method == "POST":
        form = FamilleForm(request.POST)
        if form.is_valid():
            famille = form.save()
            messages.success(request, "Famille créée.")
            return redirect("admin_produits:admin_famille_edit", pk=famille.pk)
        messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = FamilleForm()

    return render(request, "admin/products/familles/famille_add.html", {
        "form": form
    })


@login_required
def famille_create_ajax(request):
    """API AJAX: crée (ou récupère) une famille et renvoie {id, name}.

    Attendu: POST JSON {"name": "..."} ou form-data name=...
    """
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    name = None
    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads((request.body or b"").decode("utf-8") or "{}")
            name = payload.get("name")
        except json.JSONDecodeError:
            return JsonResponse({"error": "JSON invalide"}, status=400)
    else:
        name = request.POST.get("name")

    name = (name or "").strip()
    if not name:
        return JsonResponse({"error": "Nom de famille requis"}, status=400)

    if len(name) > 100:
        return JsonResponse({"error": "Nom trop long (100 caractères max)"}, status=400)

    existing = Famille.objects.filter(nom_famille__iexact=name).first()
    if existing:
        return JsonResponse({"id": existing.pk, "name": existing.nom_famille, "created": False})

    famille = Famille.objects.create(nom_famille=name)
    return JsonResponse({"id": famille.pk, "name": famille.nom_famille, "created": True})

@login_required
def famille_edit(request, pk):
    """Modifie une famille et affiche la liste des produits associés."""
    famille = get_object_or_404(Famille, pk=pk)
    produits = famille.famille.all()  # related_name="famille"

    if request.method == "POST":
        form = FamilleForm(request.POST, instance=famille)
        if form.is_valid():
            form.save()
            messages.success(request, "Famille mise à jour.")
            return redirect("admin_produits:admin_famille_edit", pk=famille.pk)
        messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = FamilleForm(instance=famille)

    return render(request, "admin/products/familles/famille_edit.html", {
        "famille": famille,
        "form": form,
        "produits": produits,
    })

@login_required
def produit_list(request):
    """Liste tous les produits avec leur famille (select_related)."""
    produits = Produit.objects.select_related("famille").all()

    return render(request, "admin/products/produit_list.html", {
        "produits": produits
    })


@login_required
@transaction.atomic
def produit_add(request):
    """Crée un produit et ses images via formset (gère le flag "produit du moment")."""
    if request.method == "POST":
        form = ProduitForm(request.POST)
        formset = ImageProduitFormSet(request.POST, request.FILES, prefix="images")

        if form.is_valid() and formset.is_valid():
            produit = form.save()
            # Identifier (via les forms) l'image cochée "du moment" (si une seule doit l'être)
            moment_instance = None
            for f in formset.forms:
                if not getattr(f, "cleaned_data", None):
                    continue
                if f.cleaned_data.get("DELETE"):
                    continue
                if f.cleaned_data.get("is_image_du_moment"):
                    moment_instance = f.instance
                    break

            images = formset.save(commit=False)
            for img in images:
                img.produit = produit
                img.save()

            for obj in formset.deleted_objects:
                obj.delete()

            # Enforcer: une seule image "du moment" sur ce produit
            if moment_instance and moment_instance.pk:
                Image_Produit.objects.filter(produit=produit).update(is_image_du_moment=False)
                Image_Produit.objects.filter(pk=moment_instance.pk, produit=produit).update(is_image_du_moment=True)

            messages.success(request, "Produit créé.")
            return redirect("admin_produits:admin_produit_edit", produit.pk)

        messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ProduitForm()
        formset = ImageProduitFormSet(prefix="images")

    return render(request, "admin/products/produit_edit.html", {
        "form": form,
        "formset": formset,
        "total_forms": formset.total_form_count(),
        "produit": None,
    })


@login_required
@transaction.atomic
def produit_edit(request, pk):
    """Modifie un produit et ses images via formset (suppression incluse)."""
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == "POST":
        form = ProduitForm(request.POST, instance=produit)
        formset = ImageProduitFormSet(request.POST, request.FILES, instance=produit, prefix="images")

        if form.is_valid() and formset.is_valid():
            form.save()

            # Identifier l'image "du moment" choisie (si présente)
            moment_instance = None
            for f in formset.forms:
                if not getattr(f, "cleaned_data", None):
                    continue
                if f.cleaned_data.get("DELETE"):
                    continue
                if f.cleaned_data.get("is_image_du_moment"):
                    moment_instance = f.instance
                    break

            instances = formset.save(commit=False)
            for inst in instances:
                inst.produit = produit
                inst.save()

            for obj in formset.deleted_objects:
                obj.delete()

            # Enforcer: une seule image "du moment" sur ce produit
            if moment_instance and moment_instance.pk:
                Image_Produit.objects.filter(produit=produit).update(is_image_du_moment=False)
                Image_Produit.objects.filter(pk=moment_instance.pk, produit=produit).update(is_image_du_moment=True)

            messages.success(request, "Produit enregistré.")
            return redirect("admin_produits:admin_produit_edit", pk=produit.pk)

        messages.error(request, "Veuillez corriger les erreurs.")
        print("PRODUIT FORM ERRORS:", form.errors)
        print("PRODUIT FORM NON FIELD ERRORS:", form.non_field_errors())
        print("IMAGE FORMSET NON FORM ERRORS:", formset.non_form_errors())
        print("IMAGE FORMSET ERRORS:", formset.errors)
    else:
        form = ProduitForm(instance=produit)
        formset = ImageProduitFormSet(instance=produit, prefix="images")

    return render(request, "admin/products/produit_edit.html", {
        "form": form,
        "formset": formset,
        "produit": produit,
        "total_forms": formset.total_form_count(),
    })


@login_required
def produit_image_form(request):
    """Retourne en JSON le HTML d'une card vide pour ajouter une image produit (AJAX)."""
    try:
        form_index = int(request.GET.get("index", 0))
        prefix = f"images-{form_index}"
        form = ImageProduitForm(prefix=prefix)

        html = '<div class="image-card">'
        # Champs cachés (ex: id_image) - généralement vide pour une nouvelle ligne, mais safe.
        for hidden in form.hidden_fields():
            html += str(hidden)
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
        html += '<button type="button" class="image-select-btn" data-image-type="produit">'
        html += '<span class="material-symbols-outlined">image</span>'
        html += 'Sélectionner une image'
        html += '</button>'
        html += str(form["image_existing"])
        html += '</div>'
        html += '<div class="image-preview-container" style="display:none; margin-top: 15px;">'
        html += '<div class="image-preview"></div>'
        html += '</div>'
        html += '</div>'
        html += '</div>'

        html += '<div class="form-group">'
        html += '<label class="form-label">Ordre</label>'
        html += str(form["ordre"])
        html += '</div>'

        html += '<div class="form-group">'
        html += '<label class="form-label">Image du moment</label>'
        html += str(form["is_image_du_moment"])
        html += '</div>'
        html += '</div>'

        return JsonResponse({"html": html})
    except Exception as exc:  # pylint: disable=broad-exception-caught
        traceback.print_exc()
        return JsonResponse({"error": str(exc)}, status=500)


@login_required
def image_produit_library(request):
    """Affiche la bibliothèque d'images produit avec pagination et usages (liens vers produits)."""
    images = Image_Produit.objects.select_related("produit").all().order_by("id_image")
    paginator = Paginator(images, 24)
    page_obj = paginator.get_page(request.GET.get("page"))
    image_data = []

    for img in page_obj.object_list:
        usages = []

        if img.produit_id:
            usages.append({
                "text": f"Produit: {img.produit.nom_produit}",
                "url": reverse("admin_produits:admin_produit_edit", kwargs={"pk": img.produit.pk}),
            })

        image_data.append({
            "image": img,
            "usages": usages,
            "is_used": len(usages) > 0,
        })

    return render(request, "admin/products/image_library.html", {
        "image_data": image_data,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "current_sort_query": "",
        "current_querystring": "",
    })


@login_required
def image_produit_delete(request, pk):
    """Supprime une image produit uniquement si elle n'est liée à aucun produit."""
    image = get_object_or_404(Image_Produit, pk=pk)

    is_used = image.produit_id is not None

    if is_used:
        messages.warning(request, "L'image est utilisée et ne peut pas être supprimée.")
    else:
        image.delete()
        messages.success(request, "Image supprimée.")

    return redirect("admin_produits:admin_produit_image_library")


@login_required
def image_produit_bulk_delete(request):
    """Supprime en masse des images produits (si non liées à un produit)."""
    if request.method != "POST":
        return redirect("admin_produits:admin_produit_image_library")

    if request.POST.get("select_all_unused") == "1":
        images = Image_Produit.objects.select_related("produit").filter(produit__isnull=True)
        deleted_count = images.count()
        if deleted_count:
            images.delete()
            messages.success(request, f"{deleted_count} image(s) supprimée(s).")
        return redirect("admin_produits:admin_produit_image_library")

    raw_ids = request.POST.getlist("selected_images")
    try:
        ids = [int(x) for x in raw_ids]
    except (TypeError, ValueError):
        messages.error(request, "Sélection invalide.")
        return redirect("admin_produits:admin_produit_image_library")

    if not ids:
        return redirect("admin_produits:admin_produit_image_library")

    images = Image_Produit.objects.select_related("produit").filter(pk__in=ids)

    deleted_count = 0
    skipped: list[str] = []

    for image in images:
        if image.produit_id is not None:
            skipped.append(image.image.url.split('/')[-1])
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

    return redirect("admin_produits:admin_produit_image_library")


@login_required
def image_produit_rename(request, pk):
    """Renomme physiquement le fichier d'image produit sur disque puis met à jour le champ ImageField."""
    image = get_object_or_404(Image_Produit, pk=pk)

    if request.method == "POST":
        new_name = request.POST.get("new_name")
        if new_name:
            old_path = os.path.join(settings.MEDIA_ROOT, image.image.name)
            dir_path = os.path.dirname(old_path)
            ext = os.path.splitext(image.image.name)[1]
            new_filename = new_name + ext
            new_path = os.path.join(dir_path, new_filename)

            if os.path.exists(old_path):
                os.rename(old_path, new_path)

            image.image.name = os.path.relpath(new_path, settings.MEDIA_ROOT)
            image.save()
            messages.success(request, "Image renommée.")

        return redirect("admin_produits:admin_produit_image_library")

    current_name = os.path.splitext(os.path.basename(image.image.name))[0]
    return render(request, "admin/products/image_rename.html", {
        "image": image,
        "current_name": current_name,
    })


@login_required
def produit_delete(request, pk):
    """Supprime un produit puis redirige vers la liste admin des produits."""
    produit = get_object_or_404(Produit, pk=pk)
    produit.delete()
    messages.success(request, "Produit supprimé.")
    return redirect("admin_produits:admin_produit_list")
