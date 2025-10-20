from django.test import TestCase
from apps.core.models import A_Propos

class AProposModelTest(TestCase):
    def setUp(self):
        self.ap = A_Propos.objects.create(titre_ap="titre test a propos", description_ap="description test a propos")

    def test_categorie_create(self):
        self.assertEqual(self.ap.titre_ap, "titre test a propos")
        self.assertEqual(self.ap.description_ap, "description test a propos")

    def test_string_repr(self):
        self.assertEqual(str(self.ap), "titre test a propos")

    def test_categorie_update(self):
        self.ap.titre_ap = "titre2 test a propos"
        self.ap.description_ap = "description2 test a propos"
        self.ap.save()

        update_categ = A_Propos.objects.get(idCat=self.ap.id_ap)
        self.assertEqual(update_categ.titre_ap, "titre2 test a propos")
        self.assertEqual(update_categ.description_ap, "description2 test a propos")

    def test_categorie_delete(self):
        self.ap.delete()
        self.assertEqual(A_Propos.objects.count(), 0)