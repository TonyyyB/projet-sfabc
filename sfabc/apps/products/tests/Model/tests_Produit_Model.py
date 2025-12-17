from django.test import TestCase
from apps.products.models import Produit, Famille


class ProduitModelTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="nom test famille")
        self.produit = Produit.objects.create(nom_produit="nom test produit", prix_produit=3.99, description_produit="description test produit", famille=self.famille)


    def test_produit_create(self):
        self.assertEqual(self.produit.nom_produit, "nom test produit")
        self.assertEqual(self.produit.prix_produit, 3.99)
        self.assertEqual(self.produit.description_produit, "description test produit")
        self.assertEqual(self.produit.is_produit_du_moment, False)
        self.assertEqual(self.produit.famille, self.famille)


    def test_string_repr(self):
        self.assertEqual(str(self.produit), "nom test produit, famille nom test famille: 3.99€")


    def test_produit_update(self):
        self.produit.nom_produit = "nom test produit2"
        self.produit.prix_produit = 45.25
        self.produit.description_produit = "description test produit2"
        self.produit.is_produit_du_moment = True
        self.produit.save()

        update_produit = Produit.objects.get(id_produit=self.produit.id_produit)
        self.assertEqual(update_produit.nom_produit, "nom test produit2")
        self.assertEqual(update_produit.prix_produit, 45.25)
        self.assertEqual(update_produit.description_produit, "description test produit2")
        self.assertEqual(update_produit.is_produit_du_moment, True)


    def test_produit_delete(self):
        self.produit.delete()
        self.assertEqual(Produit.objects.count(), 0)
        self.famille.delete()
