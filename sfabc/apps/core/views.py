from django.conf import settings as django_settings
from django.core.mail import EmailMultiAlternatives
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import FormView, ListView, TemplateView

from apps.core.models import A_Propos, Groupe_A_Propos, Image_A_Propos, Image_Service, Service, Site
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
    success_url = '/contact/confirmation/'

    def dispatch(self, request, *args, **kwargs):
        """Vérifie le rate limit avant de traiter la requête."""
        last_sent = request.session.get('last_contact_email')
        if last_sent:
            last_sent_time = timezone.datetime.fromisoformat(last_sent)
            cooldown = timezone.timedelta(hours=1)
            if timezone.now() < last_sent_time + cooldown:
                remaining = (last_sent_time + cooldown) - timezone.now()
                minutes = int(remaining.total_seconds() // 60)
                self.cooldown_remaining = minutes
            else:
                self.cooldown_remaining = None
        else:
            self.cooldown_remaining = None
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Ajoute un titre et l'état du cooldown au contexte."""
        context = super().get_context_data(**kwargs)
        context["title"] = "Contactez-moi !"
        context["cooldown_active"] = self.cooldown_remaining is not None
        context["cooldown_minutes"] = self.cooldown_remaining
        return context

    def form_valid(self, form):
        """Envoie un email à partir des champs validés puis redirige vers la page de confirmation."""
        # Vérifier le rate limit
        if self.cooldown_remaining is not None:
            form.add_error(None, "Vous avez déjà envoyé un message récemment. Veuillez réessayer plus tard.")
            return self.form_invalid(form)

        name = form.cleaned_data['name']
        sender_email = form.cleaned_data['email']
        subject_text = form.cleaned_data['subject']
        message_text = form.cleaned_data['message']

        subject = f"{name} vous contacte pour : {subject_text}"

        # Récupérer les couleurs du site
        site = Site.load()

        # Contexte pour le template email
        email_context = {
            'name': name,
            'email': sender_email,
            'subject': subject_text,
            'message': message_text,
            'site': site,
        }

        # Rendu du template HTML
        html_content = render_to_string('emails/contact_email.html', email_context)
        text_content = f"De : {name} ({sender_email})\nSujet : {subject_text}\n\n{message_text}"

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=django_settings.DEFAULT_FROM_EMAIL,
            to=[django_settings.CONTACT_RECIPIENT_EMAIL],
            reply_to=[sender_email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)

        # Enregistrer le timestamp en session
        self.request.session['last_contact_email'] = timezone.now().isoformat()

        return super().form_valid(form)


class ContactConfirmationView(TemplateView):
    """Page de confirmation après envoi du formulaire de contact."""
    template_name = 'pages/contact_confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Message envoyé"
        return context

class AProposView(ListView):
    """Vue listant les groupes "À propos" et leurs sections (avec images par emplacement)."""
    model = Groupe_A_Propos
    context_object_name = "groups"
    template_name = "pages/about.html"


    def get_queryset(self):
        """Retourne les groupes ordonnés, avec leurs sections (ordonnées) + images préchargées."""

        sections_qs = A_Propos.objects.order_by("ordre_ap", "pk").prefetch_related(
            Prefetch(
                "images",
                queryset=Image_A_Propos.objects.select_related("image").filter(position="left"),
                to_attr="images_left",
            ),
            Prefetch(
                "images",
                queryset=Image_A_Propos.objects.select_related("image").filter(position="center"),
                to_attr="images_center",
            ),
            Prefetch(
                "images",
                queryset=Image_A_Propos.objects.select_related("image").filter(position="right"),
                to_attr="images_right",
            ),
        )

        return (
            Groupe_A_Propos.objects
            .order_by("ordre_groupe", "pk")
            .prefetch_related(
                Prefetch("sections", queryset=sections_qs, to_attr="sections_list")
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
