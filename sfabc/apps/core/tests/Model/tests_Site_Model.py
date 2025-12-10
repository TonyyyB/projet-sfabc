from django.test import TestCase
from apps.core.models import Site, Image_Site
from django.core.files.uploadedfile import SimpleUploadedFile

class SiteModelTest(TestCase):
    def setUp(self):
        self.image = Image_Site.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"))
        self.site = Site.objects.create(background="#FFFFFF", foreground="#FFFFFF", police="Bookman", bandeau_hauteur=150, logo=self.image, bandeau=self.image)

    def test_site_create(self):
        self.assertEqual(self.site.background, "#FFFFFF")
        self.assertEqual(self.site.foreground, "#FFFFFF")
        self.assertEqual(self.site.police, "Bookman")
        self.assertEqual(self.site.bandeau_hauteur, 150)
        self.assertEqual(self.site.logo, self.image)
        self.assertEqual(self.site.bandeau, self.image)


    def test_string_repr(self):
        self.assertEqual(str(self.site), "<Site background: #FFFFFF, foreground: #FFFFFF, police: Bookman>")


    def test_site_update(self):
        self.site.background = "#000000"
        self.site.foreground = "#000000"
        self.site.police = "Alata"
        self.site.bandeau_hauteur = 100
        self.site.save()

        update_site = Site.objects.get(id=self.site.id)
        self.assertEqual(update_site.background, "#000000")
        self.assertEqual(update_site.foreground, "#000000")
        self.assertEqual(update_site.police, "Alata")
        self.assertEqual(update_site.bandeau_hauteur, 100)


    def test_site_delete(self):
        self.site.delete()
        self.assertEqual(Site.objects.count(), 0)
