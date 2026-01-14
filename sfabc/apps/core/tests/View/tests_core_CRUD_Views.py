from django.test import TestCase, override_settings
from django.urls import reverse
from apps.core.models import A_Propos, Service, Image_Site
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class HomeViewTest(TestCase):
    def test_home_view(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/home.html')


class ContactViewTest(TestCase):
    def test_contact_view(self):
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/contact.html')


class AProposViewTest(TestCase):
    def setUp(self):
        self.ap = A_Propos.objects.create(ordre_ap=1, titre_ap="test titre a propos", description_ap="test description a propos")


    def test_a_propos_view(self):
        response = self.client.get(reverse('core:a_propos'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/about.html')
        # Vérifie que le titre et la description du a propos soient affichés
        self.assertContains(response, 'test titre a propos')
        self.assertContains(response, 'test description a propos')
        # Vérifie que l'id associé est affiché
        self.assertContains(response, '1')
        self.ap.delete()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ServiceViewTest(TestCase):
    def setUp(self):
        self.image_site = Image_Site.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"))
        self.service = Service.objects.create(titre_service="test titre service", description_service="test description service", ordre_service=1)

        self.service.image.add(self.image_site)
    

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_service_view(self):
        response = self.client.get(reverse('core:services'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'pages/service.html')
        # Vérifie que le titre et la description du service soient affichés
        self.assertContains(response, 'test titre service')
        self.assertContains(response, 'test description service')
        # Vérifie que l'id associé est affiché
        self.assertContains(response, '1')
        self.image_site.delete()
        self.service.delete()
