from apps.reviews.models import Avis
from apps.products.models import Produit
from sortable_listview import SortableListView
from django.urls import reverse
from django.test import TestCase

class ListAvisViewTest(TestCase):
    def test_list_avis_view(self):
        produit = Produit.objects.create(nom_produit="Produit Test", description_produit="Description Test", prix_produit=10.0)
        avis1 = Avis.objects.create(pseudonyme="User1", valeur=5, message="Excellent produit!", produit=produit)
        avis2 = Avis.objects.create(pseudonyme="User2", valeur=3, message="Moyen.", produit=produit)

        response = self.client.get(reverse('reviews:avis_list', kwargs={'pk': produit.id_produit}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/reviews.html')
        self.assertContains(response, 'Excellent produit!')
        self.assertContains(response, 'Moyen.')

        avis1.delete()
        avis2.delete()
        produit.delete()