from django.core.mail import send_mail
from django.db.models import Prefetch
from django.views.generic import FormView, ListView

from apps.core.models import A_Propos, Image_A_Propos, Image_Service, Service
from apps.products.models import Image_Produit, Produit

from .forms import ContactForm


# Create your views here.

class Home(ListView):
    """Vue d'accueil listant les produits "du moment"."""
    model = Produit
    template_name = "pages/home.html"
    context_object_name = "produits_moment"

    def get_queryset(self):
        """Récupère les produits marqués "produit du moment" avec préchargement des images associées."""
        return Produit.objects.filter(is_produit_du_moment=True).prefetch_related(
            Prefetch(
                "images",
                queryset=Image_Produit.objects.filter(is_image_du_moment=True),
                to_attr="images_list",
            )
        )

    def get_context_data(self, **kwargs):
        """Construit le contexte de la page d'accueil (hérite du contexte ListView)."""
        context = super().get_context_data(**kwargs)
        return context


class ContactView(FormView):
    """Vue formulaire de contact (envoi d'email à la validation)."""
    template_name = 'pages/contact.html'
    form_class = ContactForm
    success_url = '/email-sent/'

    def get_context_data(self, **kwargs):
        """Ajoute un titre au contexte du formulaire de contact."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Contactez-moi !"
        return context

    def form_valid(self, form):
        """Envoie un email à partir des champs validés puis redirige vers la success_url."""
        subject = (
            f"{form.cleaned_data['Nom']} vous contacte pour : {form.cleaned_data['Sujet']}"
        )
        send_mail(
            subject=subject,
            message=form.cleaned_data['Message'],
            from_email=form.cleaned_data['Email'],
            recipient_list=[""],  # <-- Add your email here
            fail_silently=False,
        )
        return super().form_valid(form)

class AProposView(ListView):
    """Vue listant les sections "À propos" avec images par emplacement."""
    model = A_Propos
    context_object_name = "sections_ap"
    template_name = "pages/about.html"


    def get_queryset(self):
        """
        Retourne les sections "À propos" ordonnées, avec préchargement des images par position
        (gauche/centre/droite).
        """
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
        """Ajoute le titre de page "À propos" au contexte."""
        context = super().get_context_data(**kwargs)
        context["title"] = "À propos"
        return context

class ServiceView(ListView):
    """Vue listant les services affichés sur la page services."""
    model = Service
    context_object_name = "services"
    template_name = "pages/service.html"


    def get_queryset(self):
        """Retourne les services ordonnés, en préchargeant les images de service dans l'ordre."""
        return Service.objects.order_by("ordre_service").prefetch_related(
            Prefetch(
                "service",
                queryset=Image_Service.objects.select_related("image").order_by("ordre", "pk"),
            )
        )


    def get_context_data(self, **kwargs):
        """Ajoute le titre de page "Services" au contexte."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Services"
        return context
