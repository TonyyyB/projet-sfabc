from django.test import TestCase
from apps.reviews.models import Avis
from apps.products.models import Produit, Famille
from datetime import date

# Create your tests here.
class AvisModelTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="nom test famille")
        self.produit = Produit.objects.create(nom_produit="nom test produit", prix_produit=3.99, description_produit="description test produit", famille=self.famille)
        self.avis = Avis.objects.create(produit=self.produit, pseudonyme="test pseudonyme avis", valeur=2, message="test message avis")
    

    def test_avis_creation(self):
        self.assertEqual(self.avis.produit,    self.produit)
        self.assertEqual(self.avis.pseudonyme, "test pseudonyme avis")
        self.assertEqual(self.avis.valeur,     2)
        self.assertEqual(self.avis.date,       date.today())
        self.assertEqual(self.avis.message,    "test message avis")


    def test_string_repr(self):
        self.assertEqual(str(self.avis), "test pseudonyme avis sur nom test produit, famille nom test famille: 3.99€ : 2/5")


    def test_avis_updating(self):
        self.avis.pseudonyme = "test pseudonyme avis 2"
        self.avis.valeur = 4
        self.avis.message = "test message avis 2"
        self.avis.save()

        updated_avis:Avis = Avis.objects.get(id_note=self.avis.id_note)
        self.assertEqual(updated_avis.pseudonyme, "test pseudonyme avis 2")
        self.assertEqual(updated_avis.valeur,     4)
        self.assertEqual(updated_avis.message,    "test message avis 2")


    def test_avis_deletion(self):
        self.avis.delete()
        self.assertEqual(Avis.objects.count(), 0)
        self.produit.delete()
        self.famille.delete()
