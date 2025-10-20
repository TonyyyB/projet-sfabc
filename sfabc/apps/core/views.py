from django.shortcuts import render
from django.views.generic import *
from apps.products.models import *
from django.db.models import Prefetch

from .forms import ContactForm
from django.core.mail import send_mail
from django.shortcuts import redirect

# Create your views here.
def home(request):
    return render(request, 'pages/home.html')


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
            subject=f"{form.cleaned_data['name'] } vous contacte pour: {form.cleaned_data['subject']}",
            message=form.cleaned_data['message'],
            from_email=form.cleaned_data['email'],
            recipient_list=['']
        ),
        return super().form_valid(form)
    

