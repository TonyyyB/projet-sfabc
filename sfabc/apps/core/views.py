from django.shortcuts import render
from django.views.generic import *
from apps.products.models import *
from django.db.models import Prefetch, Max
from apps.core.models import A_Propos, Image_A_Propos, Service, Image_Site, Site, Image_Service
from apps.reviews.models import Avis
from django.contrib.auth import logout
from .forms import ContactForm, ImageSlotForm, SiteForm, ImageSiteForm, AProposForm, ServiceForm, ImageServiceFormSet, ImageServiceForm
from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect, get_object_or_404
from django.db import transaction
from django.urls import reverse
from django.http import JsonResponse
import os
from django.conf import settings
# Create your views here.

class Home(ListView):
    model = Produit
    template_name = "pages/home.html"
    context_object_name = "produits_moment"
    
    def get_queryset(self):
        return Produit.objects.filter(is_produit_du_moment=True).prefetch_related(
            Prefetch(
            "images", 
            queryset=Image_Produit.objects.filter(is_produit_du_moment=True),
            to_attr='images_list'
            )
        )
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ContactView(FormView):
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = '/email-sent/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Contactez-moi !"
        return context

    def form_valid(self, form):
        send_mail(
            subject=f"{form.cleaned_data['Nom'] } vous contacte pour: {form.cleaned_data['Sujet']}",
            message=form.cleaned_data['Message'],
            from_email=form.cleaned_data['Email'],
            recipient_list=[''], # <-- Add your email here
            fail_silently=False,
        ),
        return super().form_valid(form)

class AProposView(ListView):
    model = A_Propos
    context_object_name = "sections_ap"
    template_name = "pages/about.html"


    def get_queryset(self):
        return A_Propos.objects.order_by("ordre_ap").prefetch_related(
            Prefetch(
                "images",
                queryset=Image_A_Propos.objects.select_related("image").filter(position="left"),
                to_attr="images_left"
            ),
            Prefetch(
                "images", 
                queryset=Image_A_Propos.objects.select_related("image").filter(position="center"),
                to_attr="images_center"
            ),
            Prefetch(
                "images",
                queryset=Image_A_Propos.objects.select_related("image").filter(position="right"), 
                to_attr="images_right"
            )
        )


    def get_context_data(self, **kwargs):
        context = super(AProposView, self).get_context_data(**kwargs)
        context["title"] = "À propos"
        return context

class ServiceView(ListView):
    model = Service
    context_object_name = "services"
    template_name = "pages/service.html"


    def get_queryset(self):
        return Service.objects.order_by("ordre_service").prefetch_related("image")


    def get_context_data(self, **kwargs):
        context = super(ServiceView, self).get_context_data(**kwargs)
        context["title"] = "Services"
        return context

@login_required
def admin_dashboard(request):
    """
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
    site = Site.load()

    if request.method == "POST":
        form = SiteForm(request.POST, request.FILES, instance=site)
        image_form = ImageSiteForm(request.POST, request.FILES)

        if "add_image" in request.POST and image_form.is_valid():
            image_form.save()
            messages.success(request, "Image ajoutée avec succès.")
            return redirect("core:admin_site_edit")

        if "save_site" in request.POST and form.is_valid():
            form.save()
            messages.success(request, "Apparence du site mise à jour.")
            return redirect("core:admin_site_edit")
    else:
        form = SiteForm(instance=site)
        image_form = ImageSiteForm()

    return render(request, "admin/core/site_edit.html", {
        "form": form,
        "image_form": image_form,
        "site": site,
    })

@login_required
def apropos_list(request):
    pages = A_Propos.objects.order_by("ordre_ap")
    return render(request, "admin/core/apropos/apropos_list.html", {"pages": pages})

@login_required
@transaction.atomic
def apropos_move(request, pk, direction):
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

    return redirect("core:admin_apropos_list")

@login_required
def apropos_edit(request, pk=None):
    page = get_object_or_404(A_Propos, pk=pk) if pk else None

    positions = ["Gauche", "Centre", "Droite"]
    existing = {p: None for p in positions}

    if page:
        for img in page.images.all():
            existing[img.position] = img

    if request.method == "POST":
        form = AProposForm(request.POST, instance=page)

        slot_forms = [
            (pos, ImageSlotForm(request.POST, request.FILES, prefix=pos))
            for pos in positions
        ]

        valid = form.is_valid() and all(sf.is_valid() for _, sf in slot_forms)

        if valid:
            page = form.save(commit=False)
            
            if page.pk is None:
                max_ordre = A_Propos.objects.aggregate(
                    max_ordre=Max("ordre_ap")
                )["max_ordre"] or 0
                page.ordre_ap = max_ordre + 1
            page.save()
            for pos, sf in slot_forms:
                Image_A_Propos.objects.filter(page_ap=page, position=pos).delete()

                image = sf.cleaned_data["image"]
                upload = sf.cleaned_data["upload"]
                titre = sf.cleaned_data["titre_image"]

                if upload:
                    image = Image_Site.objects.create(image=upload)

                if image:
                    Image_A_Propos.objects.create(
                        page_ap=page,
                        image=image,
                        position=pos,
                        titre_image=titre,
                    )

            messages.success(request, "Section « À propos » enregistrée.")
            return redirect("core:admin_apropos_edit", pk=page.pk)
        else:
            messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = AProposForm(instance=page)
        slot_forms = [
            (
                pos,
                ImageSlotForm(
                    prefix=pos,
                    initial={
                        "image": existing[pos].image if existing[pos] else None,
                        "titre_image": existing[pos].titre_image if existing[pos] else "",
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
    page = get_object_or_404(A_Propos, pk=pk)
    deleted_order = page.ordre_ap
    page.delete()

    # Réajuster les ordres pour garder 1..N
    A_Propos.objects.filter(
        ordre_ap__gt=deleted_order
    ).update(ordre_ap=models.F("ordre_ap") - 1)

    messages.success(request, "Section « À propos » supprimée.")
    return redirect("core:admin_apropos_list")

@login_required
def service_list(request):
    services = Service.objects.order_by("ordre_service")
    return render(request, "admin/core/service/service_list.html", {
        "services": services
    })

@login_required
@transaction.atomic
def service_move(request, pk, direction):
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

    return redirect("core:admin_service_list")

@login_required
@transaction.atomic
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    deleted_order = service.ordre_service
    service.delete()

    Service.objects.filter(
        ordre_service__gt=deleted_order
    ).update(ordre_service=models.F("ordre_service") - 1)

    messages.success(request, "Service supprimé.")
    return redirect("core:admin_service_list")

@login_required
@transaction.atomic
def service_add(request):
    if request.method == "POST":
        form = ServiceForm(request.POST)
        formset = ImageServiceFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            service = form.save(commit=False)
            max_order = Service.objects.aggregate(Max("ordre_service"))["ordre_service__max"] or 0
            service.ordre_service = max_order + 1
            service.save()
            # Traiter tous les formulaires du formset
            for form_inst in formset.forms:
                if form_inst.cleaned_data:  # Vérifier que le formulaire a des données
                    if not form_inst.cleaned_data.get('DELETE'):
                        # Créer ou mettre à jour l'instance
                        inst = form_inst.save(commit=False)
                        inst.service = service
                        
                        # Gérer l'upload d'image
                        if form_inst.cleaned_data.get('upload'):
                            inst.image = Image_Site.objects.create(image=form_inst.cleaned_data['upload'])
                        
                        # Sauvegarder uniquement si une image est présente
                        if inst.image:
                            inst.save()
            messages.success(request, "Service ajouté.")
            return redirect("core:admin_service_edit", pk=service.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ServiceForm()
        formset = ImageServiceFormSet()
        for form_inst in formset:
            if 'DELETE' in form_inst.fields:
                form_inst.fields['DELETE'].widget.attrs['onchange'] = "if(this.checked) this.closest('.image-card').style.display='none';"

    template_form = ImageServiceForm(prefix="__prefix__")
    if 'DELETE' in template_form.fields:
        template_form.fields['DELETE'].widget.attrs['onchange'] = "if(this.checked) this.closest('.image-card').style.display='none';"
    return render(request, "admin/core/service/service_edit.html", {
        "form": form,
        "formset": formset,
        "service": None,
        "template_form": template_form,
        "total_forms": formset.total_form_count,
    })

@login_required
@transaction.atomic
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        formset = ImageServiceFormSet(request.POST, request.FILES, instance=service)
        if form.is_valid() and formset.is_valid():
            service = form.save()
            # Traiter tous les formulaires du formset
            for form_inst in formset.forms:
                if form_inst.cleaned_data:  # Vérifier que le formulaire a des données
                    if form_inst.cleaned_data.get('DELETE'):
                        # Supprimer si marqué comme suppression
                        if form_inst.instance.pk:
                            form_inst.instance.delete()
                    else:
                        # Créer ou mettre à jour l'instance
                        inst = form_inst.save(commit=False)
                        inst.service = service
                        
                        # Gérer l'upload d'image
                        if form_inst.cleaned_data.get('upload'):
                            inst.image = Image_Site.objects.create(image=form_inst.cleaned_data['upload'])
                        
                        # Sauvegarder uniquement si une image est présente
                        if inst.image:
                            inst.save()
            messages.success(request, "Service enregistré.")
            return redirect("core:admin_service_edit", pk=service.pk)
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ServiceForm(instance=service)
        formset = ImageServiceFormSet(instance=service)
        for form_inst in formset:
            if 'DELETE' in form_inst.fields:
                form_inst.fields['DELETE'].widget.attrs['onchange'] = "if(this.checked) this.closest('.image-card').style.display='none';"

    template_form = ImageServiceForm(prefix="__prefix__")
    if 'DELETE' in template_form.fields:
        template_form.fields['DELETE'].widget.attrs['onchange'] = "if(this.checked) this.closest('.image-card').style.display='none';"
    return render(request, "admin/core/service/service_edit.html", {
        "form": form,
        "formset": formset,
        "service": service,
        "template_form": template_form,
        "total_forms": formset.total_form_count,
    })

@login_required
def image_library(request):
    images = Image_Site.objects.all()
    image_data = []
    for img in images:
        usages = []
        # Check if used in Site
        site = Site.load()
        if site.logo == img:
            usages.append({
                'text': "Logo du site",
                'url': reverse('core:admin_site_edit')
            })
        if site.bandeau == img:
            usages.append({
                'text': "Bandeau du site", 
                'url': reverse('core:admin_site_edit')
            })
        # Check in A_Propos
        apropos_images = Image_A_Propos.objects.filter(image=img).select_related('page_ap')
        for ap_img in apropos_images:
            usages.append({
                'text': f"Page À propos: {ap_img.page_ap.titre_ap}",
                'url': reverse('core:admin_apropos_edit', kwargs={'pk': ap_img.page_ap.pk})
            })
        # Check in Services
        service_images = Image_Service.objects.filter(image=img).select_related('service')
        for svc_img in service_images:
            usages.append({
                'text': f"Service: {svc_img.service.titre_service}",
                'url': reverse('core:admin_service_edit', kwargs={'pk': svc_img.service.pk})
            })
        image_data.append({
            'image': img,
            'usages': usages,
            'is_used': len(usages) > 0
        })
    return render(request, "admin/core/image_library.html", {"image_data": image_data})

@login_required
def image_delete(request, pk):
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
    return redirect("core:admin_image_library")

@login_required
def image_rename(request, pk):
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
        return redirect("core:admin_image_library")
    return render(request, "admin/core/image_rename.html", {"image": image})

@login_required
def image_api(request):
    """API pour récupérer la liste des images pour le sélecteur"""
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
def logout_view(request):
    """
    Vue pour la déconnexion de l'administration
    """
    logout(request)
    return render(request, 'admin/logout.html')
