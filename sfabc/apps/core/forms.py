from django import forms


class ContactForm(forms.Form):
    """Formulaire de contact (nom, email, sujet, message)."""
    name = forms.CharField(required=True, max_length=100)
    email = forms.EmailField(required=True)
    subject = forms.CharField(max_length=200, required=True)
    message = forms.CharField(max_length=2000, widget=forms.Textarea)
