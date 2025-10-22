from django.shortcuts import render
from django.views.generic import *
from apps.core.models import A_Propos, Image_AP
from apps.products.models import *
from django.db.models import Prefetch

from .forms import ContactForm
from django.core.mail import send_mail
from django.shortcuts import redirect

class AProposView(ListView):
    model = A_Propos
    context_object_name = "infos"
    template_name = "pages/about.html"


    def get_queryset(self):
        return A_Propos.objects.order_by("ordre_ap").prefetch_related("page_ap__image")


    def get_context_data(self, **kwargs):
        context = super(AProposView, self).get_context_data(**kwargs)
        context["title"] = "À propos"
        return context

class Home(ListView):
    model = Produit
    template_name = "pages/home.html"
    context_object_name = "produits_moment"
    
    def get_queryset(self):
        return Produit.objects.filter(is_produit_du_moment = True).prefetch_related(Prefetch("images_produit", queryset=Image_Produit.objects.filter(is_produit_du_moment = True).select_related("image"), to_attr='images_list'))
    
    def get_context_data(self, **kwargs):
        context = super(Home, self).get_context_data(**kwargs)
        context['title'] = "Découvrez mes produits"
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
    

    
