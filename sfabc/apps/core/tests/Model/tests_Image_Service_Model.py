from django.test import TestCase, override_settings
from apps.core.models import Image_Service, Image_Site, Service
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageServiceModelTest(TestCase):
    def setUp(self):
        self.image = Image_Site.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"))
        self.service = Service.objects.create(titre_service="titre test service", description_service="description test service", ordre_service=1)
        self.image_service = Image_Service.objects.create(image=self.image, service=self.service, titre_image="titre test image service")
    

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_image_service_create(self):
        self.assertEqual(self.image_service.titre_image, "titre test image service")
        self.assertEqual(self.image_service.image, self.image)
        self.assertEqual(self.image_service.service, self.service)


    def test_string_repr(self):
        self.assertEqual(str(self.image_service), "service titre test service avec des image_test1.png")


    def test_image_service_update(self):
        self.image_service.titre_image = "titre2 test image service"
        self.image_service.save()

        update_image_service = Image_Service.objects.get(image=self.image, service=self.service)
        self.assertEqual(update_image_service.titre_image, "titre2 test image service")


    def test_image_service_delete(self):
        self.image_service.delete()
        self.image.delete()
        self.service.delete()
        self.assertEqual(Image_Service.objects.count(), 0)
