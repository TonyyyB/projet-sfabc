from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import *
from .admin_forms import *
from django.contrib import messages
from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.db import transaction

@login_required
def image_produit_api(request):
    """API pour récupérer la liste des images pour le sélecteur"""
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
    familles = Famille.objects.all().order_by("nom_famille")

    return render(request, "admin/products/familles/famille_list.html", {
        "familles": familles
    })
    
@login_required
def famille_add(request):
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
def famille_edit(request, pk):
    famille = get_object_or_404(Famille, pk=pk)
    produits = famille.famille.all()  # related_name="famille"

    if request.method == "POST":
        form = FamilleForm(request.POST, instance=famille)
        if form.is_valid():
            form.save()
            messages.success(request, "Famille mise à jour.")
            return redirect("admin_core:admin_famille_edit", pk=famille.pk)
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
    produits = Produit.objects.select_related("famille").all()

    return render(request, "admin/products/produit_list.html", {
        "produits": produits
    })


@login_required
@transaction.atomic
def produit_add(request):
    if request.method == "POST":
        form = ProduitForm(request.POST)
        formset = ImageProduitFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            produit = form.save()
            images = formset.save(commit=False)

            Image_Produit.objects.filter(
                produit=produit, is_produit_du_moment=True
            ).update(is_produit_du_moment=False)

            for img in images:
                img.produit = produit
                if img.is_produit_du_moment:
                    Image_Produit.objects.filter(
                        produit=produit
                    ).update(is_produit_du_moment=False)
                img.save()

            messages.success(request, "Produit créé.")
            return redirect("admin_produits:admin_produit_edit", produit.pk)

        messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ProduitForm()
        formset = ImageProduitFormSet()

    return render(request, "admin/products/produit_edit.html", {
        "form": form,
        "formset": formset,
        "total_forms": len(formset),
        "produit": None,
    })


@login_required
@transaction.atomic
def produit_edit(request, pk):
    produit = get_object_or_404(Produit, pk=pk)

    if request.method == "POST":
        form = ProduitForm(request.POST, instance=produit)
        formset = ImageProduitFormSet(request.POST, request.FILES, instance=produit)

        if form.is_valid() and formset.is_valid():
            form.save()

            if any(
                f.cleaned_data.get("is_produit_du_moment")
                for f in formset.forms
                if f.cleaned_data and not f.cleaned_data.get("DELETE")
            ):
                Image_Produit.objects.filter(
                    produit=produit
                ).update(is_produit_du_moment=False)

            instances = formset.save(commit=False)
            for inst in instances:
                inst.produit = produit
                inst.save()

            for obj in formset.deleted_objects:
                obj.delete()

            messages.success(request, "Produit enregistré.")
            return redirect("admin_produits:produit_edit", produit.pk)

        messages.error(request, "Veuillez corriger les erreurs.")
    else:
        form = ProduitForm(instance=produit)
        formset = ImageProduitFormSet(instance=produit)

    return render(request, "admin/products/produit_edit.html", {
        "form": form,
        "formset": formset,
        "produit": produit,
        "total_forms": len(formset)
    })


@login_required
def produit_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    produit.delete()
    messages.success(request, "Produit supprimé.")
    return redirect("admin_produits:produit_list")