from django.test import TestCase
from apps.reviews.models import Avis, Reponse
from apps.products.models import Produit, Famille
from datetime import date

# Create your tests here.
class ReponseModelTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="nom test famille")
        self.produit = Produit.objects.create(nom_produit="nom test produit", prix_produit=3.99, description_produit="description test produit", famille=self.famille)
        self.avis = Avis.objects.create(produit=self.produit, pseudonyme="test pseudonyme avis", valeur=2, message="test message avis")
        self.reponse = Reponse.objects.create(avis=self.avis, message="test message reponse")
    

    def test_reponse_creation(self):
        self.assertEqual(self.reponse.avis,    self.avis)
        self.assertEqual(self.reponse.date,    date.today())
        self.assertEqual(self.reponse.message, "test message reponse")


    def test_string_repr(self):
        self.assertEqual(str(self.reponse), "Réponse à test pseudonyme avis sur nom test produit, famille nom test famille: 3.99€ : 2/5")


    def test_reponse_updating(self):
        self.reponse.message = "test message reponse 2"
        self.reponse.save()

        updated_reponse = Reponse.objects.get(id_reponse=self.reponse.id_reponse)
        self.assertEqual(updated_reponse.message, "test message reponse 2")


    def test_reponse_deletion(self):
        self.reponse.delete()
        self.assertEqual(Reponse.objects.count(), 0)
        self.avis.delete()
        self.produit.delete()
        self.famille.delete()
