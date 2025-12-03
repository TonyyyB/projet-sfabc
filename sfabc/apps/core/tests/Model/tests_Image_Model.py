from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.models import Image_Site
from sfabc.settings import BASE_DIR
import os

class ImageModelTest(TestCase):
    def setUp(self):
        self.image = Image_Site.objects.create(image=None)


    def tearDown(self):
        if self.image.image:
            os.remove(self.image.image.path)


    def test_image_update(self):
        self.image.image = SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png")
        self.image.save()

        update_img = Image_Site.objects.get(id_image=self.image.id_image)
        self.assertEqual(update_img.image.url, "/media/images/site/image_test1.png")
        self.assertEqual(str(self.image), "image_test1.png")


    def test_image_delete(self):
        self.image.delete()
        self.assertEqual(Image_Site.objects.count(), 0)