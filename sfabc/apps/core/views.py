from django.shortcuts import render
from django.views.generic import *

from .forms import ContactForm
from django.core.mail import send_mail
from django.shortcuts import redirect

# Create your views here.
def home(request):
    return render(request, 'pages/home.html', {"title":"Coucou"})
