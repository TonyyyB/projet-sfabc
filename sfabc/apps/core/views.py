from django.shortcuts import render
from django.views.generic import *
from apps.products.models import *
from django.db.models import Prefetch
from apps.core.models import A_Propos, Image_A_Propos, Service, Image_Site
from .forms import ContactForm
from django.core.mail import send_mail
from django.shortcuts import redirect

from .forms import ContactForm
from django.core.mail import send_mail
from django.shortcuts import redirect

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
