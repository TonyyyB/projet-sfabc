from django.test import TestCase, override_settings
from apps.core.models import Image_A_Propos, Image_Site, A_Propos
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageAPModelTest(TestCase):
    def setUp(self):
        self.image = Image_Site.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"))
        self.ap = A_Propos.objects.create(titre_ap="titre test a propos", description_ap="description test a propos", ordre_ap=1)
        self.image_ap = Image_A_Propos.objects.create(image=self.image, page_ap=self.ap, titre_image="titre test image a propos", position="Droite")
    

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_categorie_create(self):
        self.assertEqual(self.image_ap.titre_image, "titre test image a propos")
        self.assertEqual(self.image_ap.position, "Droite")
        self.assertEqual(self.image_ap.image, self.image)
        self.assertEqual(self.image_ap.page_ap, self.ap)


    def test_string_repr(self):
        self.assertEqual(str(self.image_ap), "titre test a propos - titre test image a propos")


    def test_categorie_update(self):
        self.image_ap.titre_image = "titre2 test image a propos"
        self.image_ap.position = "Gauche"
        self.image_ap.save()

        update_image_ap = Image_A_Propos.objects.get(image=self.image, page_ap=self.ap)
        self.assertEqual(update_image_ap.titre_image, "titre2 test image a propos")
        self.assertEqual(update_image_ap.position, "Gauche")


    def test_categorie_delete(self):
        self.image_ap.delete()
        self.image.delete()
        self.ap.delete()
        self.assertEqual(Image_A_Propos.objects.count(), 0)
