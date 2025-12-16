from django.test import TestCase
from apps.products.models import Famille


class FamilleModelTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="nom test famille")


    def test_famille_create(self):
        self.assertEqual(self.famille.nom_famille, "nom test famille")


    def test_string_repr(self):
        self.assertEqual(str(self.famille), "nom test famille")


    def test_famille_update(self):
        self.famille.nom_famille = "nom test famille2"
        self.famille.save()

        update_famille = Famille.objects.get(id_famille=self.famille.id_famille)
        self.assertEqual(update_famille.nom_famille, "nom test famille")


    def test_famille_delete(self):
        self.famille.delete()
        self.assertEqual(Famille.objects.count(), 0)
