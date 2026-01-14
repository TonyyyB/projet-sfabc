from django.test import TestCase
from django.urls import reverse, resolve
from apps.core.views import Home, ContactView, AProposView, ServiceView


class HomeUrlsTest(TestCase):
    # Test URL
    def test_home_url_is_resolved(self):
        url = reverse('core:home')
        self.assertEqual(resolve(url).view_name, 'core:home')
        self.assertEqual(resolve(url).func.view_class, Home)


    # Test code d'erreur
    def test_home_response_code(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)


class ContactUrlsTest(TestCase):
    # Test URL
    def test_contact_url_is_resolved(self):
        url = reverse('core:contact')
        self.assertEqual(resolve(url).view_name, 'core:contact')
        self.assertEqual(resolve(url).func.view_class, ContactView)


    # Test code d'erreur
    def test_contact_response_code(self):
        response = self.client.get(reverse('core:contact'))
        self.assertEqual(response.status_code, 200)


class AProposUrlsTest(TestCase):
    # Test URL
    def test_a_propos_url_is_resolved(self):
        url = reverse('core:a_propos')
        self.assertEqual(resolve(url).view_name, 'core:a_propos')
        self.assertEqual(resolve(url).func.view_class, AProposView)


    # Test code d'erreur
    def test_a_propos_response_code(self):
        response = self.client.get(reverse('core:a_propos'))
        self.assertEqual(response.status_code, 200)


class ServiceUrlsTest(TestCase):
    # Test URL
    def test_service_url_is_resolved(self):
        url = reverse('core:services')
        self.assertEqual(resolve(url).view_name, 'core:services')
        self.assertEqual(resolve(url).func.view_class, ServiceView)


    # Test code d'erreur
    def test_service_response_code(self):
        response = self.client.get(reverse('core:services'))
        self.assertEqual(response.status_code, 200)
