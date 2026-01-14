from django.test import TestCase, override_settings
from apps.core.models import A_Propos
import tempfile
import shutil


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class AProposModelTest(TestCase):
    def setUp(self):
        self.ap = A_Propos.objects.create(titre_ap="titre test a propos", description_ap="description test a propos", ordre_ap=1)


    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_ap_create(self):
        self.assertEqual(self.ap.titre_ap, "titre test a propos")
        self.assertEqual(self.ap.description_ap, "description test a propos")
        self.assertEqual(self.ap.ordre_ap, 1)


    def test_string_repr(self):
        self.assertEqual(str(self.ap), "titre test a propos")


    def test_ap_update(self):
        self.ap.titre_ap = "titre2 test a propos"
        self.ap.description_ap = "description2 test a propos"
        self.ap.ordre_ap = 2
        self.ap.save()

        update_categ = A_Propos.objects.get(id_ap=self.ap.id_ap)
        self.assertEqual(update_categ.titre_ap, "titre2 test a propos")
        self.assertEqual(update_categ.description_ap, "description2 test a propos")
        self.assertEqual(update_categ.ordre_ap, 2)


    def test_ap_delete(self):
        self.ap.delete()
        self.assertEqual(A_Propos.objects.count(), 0)
