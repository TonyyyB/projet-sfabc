from apps.reviews.views import *
from django.test import TestCase
from django.urls import reverse, resolve

class ListAvisUrlsTest(TestCase):
    # Test URL
    def test_liste_avis_url_is_resolved(self):
        url = reverse('reviews:liste_avis')
        self.assertEqual(resolve(url).view_name, 'reviews:liste_avis')
        self.assertEqual(resolve(url).func.view_class, ReviewListView)


    # Test code d'erreur
    def test_liste_avis_response_code(self):
        response = self.client.get(reverse('reviews:liste_avis'))
        self.assertEqual(response.status_code, 200)