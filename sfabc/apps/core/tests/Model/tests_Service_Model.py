from django.test import TestCase
from apps.core.models import Service, Image_Site
from django.core.files.uploadedfile import SimpleUploadedFile

class ServiceModelTest(TestCase):
    def setUp(self):
        self.image_site = Image_Site.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"))
        self.service = Service.objects.create(titre_service="titre test service", description_service="description test service", ordre_service=1)

        self.service.image.add(self.image_site)


    def test_categorie_create(self):
        self.assertEqual(self.service.titre_service, "titre test service")
        self.assertEqual(self.service.description_service, "description test service")
        self.assertEqual(self.service.ordre_service, 1)
        self.assertIn(self.image_site, self.service.image.all())


    def test_string_repr(self):
        self.assertEqual(str(self.service), "titre test service")


    def test_categorie_update(self):
        self.service.titre_service = "titre2 test service"
        self.service.description_service = "description2 test service"
        self.service.ordre_service = 2
        self.service.save()

        update_service = Service.objects.get(id_service=self.service.id_service)
        self.assertEqual(update_service.titre_service, "titre2 test service")
        self.assertEqual(update_service.description_service, "description2 test service")
        self.assertEqual(update_service.ordre_service, 2)


    def test_categorie_delete(self):
        self.image_site.delete()
        self.service.delete()
        self.assertEqual(Service.objects.count(), 0)
