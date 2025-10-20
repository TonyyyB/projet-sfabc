from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.models import Image

class ImageModelTest(TestCase):
    def setUp(self):
        self.image = Image.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=open("image_test1", 'rb').read()))

    def test_categorie_create(self):
        self.assertEqual(self.image.titre_ap, "titre test a propos")
        self.assertEqual(self.image.description_ap, "description test a propos")

    def test_string_repr(self):
        self.assertEqual(str(self.image), "titre test a propos")

    def test_categorie_update(self):
        self.image.titre_ap = "titre2 test a propos"
        self.image.description_ap = "description2 test a propos"
        self.image.save()

        update_categ = Image.objects.get(idCat=self.image.id_ap)
        self.assertEqual(update_categ.titre_ap, "titre2 test a propos")
        self.assertEqual(update_categ.description_ap, "description2 test a propos")

    def test_categorie_delete(self):
        self.image.delete()
        self.assertEqual(Image.objects.count(), 0)