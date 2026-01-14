from apps.reviews.models import Avis
from apps.products.models import Produit, Famille
from sortable_listview import SortableListView
from django.urls import reverse
from django.test import TestCase

class ListAvisViewTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="Famille Test")
        self.produit = Produit.objects.create(nom_produit="Produit Test", description_produit="Description Test", prix_produit=10.0, famille=self.famille)
        self.avis1 = Avis.objects.create(pseudonyme="User1", valeur=5, message="Excellent produit!", produit=self.produit)
        self.avis2 = Avis.objects.create(pseudonyme="User2", valeur=3, message="Moyen.", produit=self.produit)


    def test_list_avis_view(self):
        response = self.client.get(reverse('products:reviews:liste_avis', kwargs={'pk': self.produit.id_produit}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/reviews.html')
        self.assertContains(response, 'Excellent produit!')
        self.assertContains(response, 'Moyen.')

        self.avis1.delete()
        self.avis2.delete()
        self.produit.delete()
