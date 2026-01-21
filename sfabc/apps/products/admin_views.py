import os
import traceback
import json

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
