import os
import traceback

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.core.models import (
    A_Propos,
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
    ImageServiceForm,
    ImageServiceFormSet,
    ImageSiteForm,
    ImageSlotForm,
    ServiceForm,
    SiteForm,
)

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
    })

EMPLACEMENT_AP = {
    "Gauche": "left",
    "Centre": "center",
    "Droite": "right",
}

@login_required
def apropos_list(request):
    """Liste les sections "À propos" triées par ordre d'affichage."""
    pages = A_Propos.objects.order_by("ordre_ap")
    return render(request, "admin/core/apropos/apropos_list.html", {"pages": pages})

@login_required
@transaction.atomic
def apropos_move(request, pk, direction):
    """Change l'ordre d'une section "À propos" en échangeant sa position avec la section voisine (up/down)."""
    page = get_object_or_404(A_Propos, pk=pk)

    if direction == "up":
        swap = (
            A_Propos.objects
            .filter(ordre_ap__lt=page.ordre_ap)
            .order_by("-ordre_ap")
            .first()
        )
    else:  # down
        swap = (
            A_Propos.objects
            .filter(ordre_ap__gt=page.ordre_ap)
            .order_by("ordre_ap")
            .first()
        )

    if swap:
        page.ordre_ap, swap.ordre_ap = swap.ordre_ap, page.ordre_ap
        page.save()
        swap.save()

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

        print(request.POST)

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
                max_ordre = A_Propos.objects.aggregate(
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
                    print(position)
                    Image_A_Propos.objects.create(
                        page_ap=page,
                        image=image,
                        position=EMPLACEMENT_AP[position],
                        titre_image=titre,
                    )

            messages.success(request, "Section « À propos » enregistrée.")
            return redirect("admin_core:admin_apropos_edit", pk=page.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
        print("FORM PRINCIPAL ERRORS:", form.errors)

        for pos, sf in slot_forms:
            print(f"SLOT {pos} ERRORS:", sf.errors)
            print(f"SLOT {pos} NON FIELD ERRORS:", sf.non_field_errors())
            print(f"SLOT {pos} CLEANED:", getattr(sf, "cleaned_data", None))
    else:
        form = AProposForm(instance=page)
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
        print(slot_forms)
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
    page.delete()

    # Réajuster les ordres pour garder 1..N
    A_Propos.objects.filter(
        ordre_ap__gt=deleted_order
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
    """API: renvoie la liste des images du site (id/nom/url) pour le sélecteur."""
    images = Image_Site.objects.all().order_by('image')
    image_data = []

    for img in images:
        image_data.append({
            'id': img.id_image,
            'name': str(img),
            'url': img.image.url
        })

    return JsonResponse({'images': image_data})

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
        # Pas besoin de form.id pour les nouvelles entrées
        html += '<label class="delete-btn" onclick="removeImage(this)">'
        html += '<span class="material-symbols-outlined">close</span>'
        html += '</label>'
        html += '<div class="form-group">'
        html += '<label class="form-label">Image existante</label>'
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
