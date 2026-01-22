import os
import traceback
import json
import csv
import unicodedata
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
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


def _parse_produits_csv(file_bytes: bytes) -> list[dict]:
    """Parse un CSV Produits avec colonnes:
    - Famille
    - Nom
    - Photos (liste de noms séparés par ';', ou vide)
    - Description
    - Prix

    NOTE: si le CSV utilise ';' comme séparateur, le champ Photos doit être correctement quoté
    (car il contient aussi des ';').
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

    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return []

    # Essayer ',' puis ';' (le module csv gère les champs quotés)
    for delimiter in (",", ";"):
        reader = csv.reader(lines, delimiter=delimiter)
        try:
            header = next(reader)
        except StopIteration:
            return []

        header_norm = [_normalize_header(h) for h in header]
        required = {"famille", "nom", "photos", "description", "prix"}
        if not required.issubset(set(header_norm)):
            continue

        idx = {name: header_norm.index(name) for name in required}
        rows: list[dict] = []
        for row in reader:
            if not row or all(not (c or "").strip() for c in row):
                continue
            # Certaines lignes peuvent être plus courtes
            def get(name: str) -> str:
                i = idx[name]
                return (row[i] if i < len(row) else "").strip()

            famille = get("famille")
            nom = get("nom")
            photos_raw = get("photos")
            description = get("description")
            prix_raw = get("prix")

            photos = []
            if photos_raw:
                photos = []
                for p in photos_raw.split(";"):
                    p = p.strip()
                    if not p:
                        continue
                    try:
                        photos.append(_safe_basename(p))
                    except ValueError as exc:
                        raise ValueError(f"Nom de photo invalide: {p}") from exc

            rows.append({
                "famille": famille,
                "nom": nom,
                "photos": photos,
                "description": description,
                "prix": prix_raw,
            })

        return rows

    raise ValueError("Colonnes CSV requises: Famille, Nom, Photos, Description, Prix")


@login_required
def import_produits(request):
    """Import CSV des produits, avec sélection/import d'images manquantes via ImageSelector."""
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

            existing_familles = {
                (name or "").strip().lower()
                for name in Famille.objects.values_list("nom_famille", flat=True)
            }

            resolved_rows = []
            missing_images = 0
            missing_familles = 0

            for r in rows:
                fam_name = (r.get("famille") or "").strip()
                if fam_name and fam_name.lower() not in existing_familles:
                    missing_familles += 1

                photo_cells = []
                for name in (r.get("photos") or []):
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
                    "nom": (r.get("nom") or "").strip(),
                    "description": (r.get("description") or "").strip(),
                    "prix": (r.get("prix") or "").strip(),
                    "photos": photo_cells,
                })

            return render(request, "admin/products/import_produits.html", {
                "step": "resolve",
                "rows": resolved_rows,
                "rows_json": json.dumps(rows, ensure_ascii=False),
                "missing_images": missing_images,
                "missing_familles": missing_familles,
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

            created = 0
            warnings = 0

            # Import transactionnel
            with transaction.atomic():
                for idx, r in enumerate(rows):
                    fam_name = str(r.get("famille", "")).strip()
                    nom = str(r.get("nom", "")).strip()
                    description = str(r.get("description", "")).strip()
                    prix_raw = str(r.get("prix", "")).strip()

                    if not fam_name or not nom:
                        warnings += 1
                        continue

                    famille, _ = Famille.objects.get_or_create(nom_famille=fam_name)

                    prix_value = None
                    if prix_raw:
                        try:
                            prix_value = Decimal(prix_raw.replace(",", "."))
                        except (InvalidOperation, ValueError):
                            prix_value = None
                            warnings += 1

                    produit = Produit.objects.create(
                        famille=famille,
                        nom_produit=nom,
                        description_produit=description,
                        prix_produit=prix_value,
                    )

                    # Associer les images choisies (y compris celles pré-remplies si trouvées)
                    photos = r.get("photos") or []
                    if isinstance(photos, list):
                        for photo_i, photo in enumerate(photos):
                            field = f"rows-{idx}-photo-{photo_i}-image_existing"
                            image_id = (request.POST.get(field) or "").strip()
                            if not image_id:
                                continue
                            try:
                                img = Image_Produit.objects.get(pk=int(image_id))
                            except Exception:  # pylint: disable=broad-exception-caught
                                warnings += 1
                                continue
                            img.produit = produit
                            img.save(update_fields=["produit"])

                    created += 1

            messages.success(request, f"{created} produit(s) importé(s).")
            if warnings:
                messages.warning(request, "Certaines lignes/champs n'ont pas pu être importés correctement.")
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

        for idx, upload in enumerate(files):
            original_name = _safe_basename(upload.name)
            base, ext = os.path.splitext(original_name)

            wanted = None
            if isinstance(desired_names, list) and idx < len(desired_names):
                wanted = str(desired_names[idx] or "").strip()

            if wanted:
                wanted = _safe_basename(wanted)
                wanted_base, wanted_ext = os.path.splitext(wanted)
                if wanted_ext == "":
                    filename = f"{wanted_base}{ext}"
                else:
                    filename = wanted
            else:
                filename = original_name

            final_names.append(filename)

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
    """API: renvoie la liste des images produit (id/nom/url) pour le sélecteur."""
    images = Image_Produit.objects.all().order_by('image')
    image_data = []

    for img in images:
        image_data.append({
            'id': img.id_image,
            'name': img.image.url.split('/')[-1],
            'url': img.image.url
        })

    return JsonResponse({'images': image_data})

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
                if f.cleaned_data.get("is_produit_du_moment"):
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
                Image_Produit.objects.filter(produit=produit).update(is_produit_du_moment=False)
                Image_Produit.objects.filter(pk=moment_instance.pk, produit=produit).update(is_produit_du_moment=True)

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
                if f.cleaned_data.get("is_produit_du_moment"):
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
                Image_Produit.objects.filter(produit=produit).update(is_produit_du_moment=False)
                Image_Produit.objects.filter(pk=moment_instance.pk, produit=produit).update(is_produit_du_moment=True)

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
        html += '<label class="delete-btn" onclick="removeImage(this)">'
        html += '<span class="material-symbols-outlined">close</span>'
        html += '</label>'

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
        html += '<label class="form-label">Image du moment</label>'
        html += str(form["is_produit_du_moment"])
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
