from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from apps.products.views import DetailProduitView, ProduitListView
from apps.products.models import Produit, Famille

class ProduitUrlsTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="FamillePourTest")
        self.produit = Produit.objects.create(nom_produit="ProduitPourTest", prix_produit=27, description_produit = "DescriptionProduit", is_produit_du_moment="False", famille=self.famille)
        self.user = User.objects.create_user(username='testuser', password='secret')
        self.client.login(username='testuser', password='secret')


    # Test URL
    def test_categorie_list_url_is_resolved(self):
        url = reverse('products:liste_produits')
        self.assertEqual(resolve(url).view_name, 'products:liste_produits')
        self.assertEqual(resolve(url).func.view_class, ProduitListView)


    def test_categorie_detail_url_is_resolved(self):
        url = reverse('products:detail_produit', args=[self.produit.id_produit])
        self.assertEqual(resolve(url).view_name, 'products:detail_produit')
        self.assertEqual(resolve(url).func.view_class, DetailProduitView)


    # Test code d'erreur
    def test_categorie_list_response_code(self):
        response = self.client.get(reverse('products:liste_produits'))
        self.assertEqual(response.status_code, 200)


    def test_categorie_detail_response_code(self):
        url = reverse('products:detail_produit', args=[self.produit.id_produit])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


    def test_categorie_detail_response_code_KO(self):
        url = reverse('products:detail_produit', args=[9999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
