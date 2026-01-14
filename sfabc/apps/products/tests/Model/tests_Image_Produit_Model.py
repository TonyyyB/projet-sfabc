from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.products.models import Image_Produit, Produit, Famille
import tempfile
import shutil


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageProduitModelTest(TestCase):
    def setUp(self):
        self.famille = Famille.objects.create(nom_famille="nom test famille")
        self.produit = Produit.objects.create(nom_produit="nom test produit", prix_produit=3.99, description_produit="description test produit", famille=self.famille)
        self.image_produit = Image_Produit.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"), produit=self.produit)


    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_image_produit_create(self):
        self.assertEqual(self.image_produit.produit, self.produit)


    def test_string_repr(self):
        self.assertEqual(str(self.image_produit), "Image images/produits/image_test1.png associée à nom test produit")


    def test_image_produit_update(self):
        self.updated_produit = Produit.objects.create(nom_produit="nom test produit2", prix_produit=45.99, description_produit="description test produit2", famille=self.famille)
        self.image_produit.produit = self.updated_produit
        self.image_produit.save()

        update_image = Image_Produit.objects.get(image=self.image_produit.image, produit=self.updated_produit)
        self.assertEqual(update_image.produit, self.image_produit.produit)


    def test_image_produit_delete(self):
        self.image_produit.delete()
        self.assertEqual(Image_Produit.objects.count(), 0)
        self.produit.delete()
        self.famille.delete()
