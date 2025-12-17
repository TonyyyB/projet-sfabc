from django.test import TestCase
from django.urls import reverse
from apps.products.models import Produit, Famille
from django.core.files.uploadedfile import SimpleUploadedFile


class ProduitDetailViewTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="FamillePourTest")
        self.produit = Produit.objects.create(nom_produit="ProduitPourTest", prix_produit=27, description_produit = "DescriptionProduit", is_produit_du_moment="False", famille=self.famille)


    def test_produit_detail_view(self):
        response = self.client.get(reverse('products:detail_produit', args=[self.produit.id_produit]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'products/detail.html')
        self.assertContains(response, 'ProduitPourTest')
        self.assertContains(response, '27')
        self.assertContains(response, 'DescriptionProduit')
        self.assertContains(response, '1')
