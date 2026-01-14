from apps.reviews.views import *
from apps.products.models import Produit, Famille
from django.test import TestCase
from django.urls import reverse, resolve

class ListAvisUrlsTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="Famille Test")
        self.produit = Produit.objects.create(nom_produit="Produit Test", description_produit="Description Test", prix_produit=10.0, famille=self.famille)
        self.avis = Avis.objects.create(pseudonyme="User1", valeur=5, message="Excellent produit!", produit=self.produit)


    # Test URL
    def test_liste_avis_url_is_resolved(self):
        url = reverse('products:reviews:liste_avis', args=[self.produit.id_produit])
        self.assertEqual(resolve(url).view_name, 'products:reviews:liste_avis')
        self.assertEqual(resolve(url).func.view_class, ReviewListView)


    # Test code d'erreur
    def test_liste_avis_response_code(self):
        response = self.client.get(reverse('products:reviews:liste_avis', args=[self.produit.id_produit]))
        self.assertEqual(response.status_code, 200)
