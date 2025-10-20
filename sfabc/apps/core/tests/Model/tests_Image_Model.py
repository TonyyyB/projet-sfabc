from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.core.models import Image
from sfabc.settings import BASE_DIR
import os

class ImageModelTest(TestCase):
    def setUp(self):
        self.image = Image.objects.create(image=None)

    
    def tearDown(self):
        if self.image.image:
            os.remove(self.image.image.path)


    def test_image_update(self):
        self.image.image = SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png")
        self.image.save()

        update_img = Image.objects.get(id_image=self.image.id_image)
        self.assertEqual(update_img.image.url, "/media/images/image_test1.png")
        self.assertEqual(str(self.image), "/media/images/image_test1.png")


    def test_image_delete(self):
        self.image.delete()
        self.assertEqual(Image.objects.count(), 0)