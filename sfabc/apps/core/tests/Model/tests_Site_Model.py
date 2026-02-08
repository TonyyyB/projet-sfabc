from django.test import TestCase, override_settings
from apps.core.models import Site, Image_Site
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import shutil


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class SiteModelTest(TestCase):
    def setUp(self):
        self.image = Image_Site.objects.create(image=SimpleUploadedFile(name="image_test1.png", content=b'', content_type="image/png"))
        self.site = Site.objects.create(
            page_foreground="#111111",
            page_background="#FFFFFF",
            card_background="#F0F0F0",
            carousel_background="#FAFAFA",
            text_title="#222222",
            police="Bookman",
            bandeau_hauteur=150,
            logo=self.image,
            bandeau=self.image,
        )


    def tearDown(self):
        super().tearDown()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)


    def test_site_create(self):
        self.assertEqual(self.site.page_background, "#FFFFFF")
        self.assertEqual(self.site.page_foreground, "#111111")
        self.assertEqual(self.site.card_background, "#F0F0F0")
        self.assertEqual(self.site.police, "Bookman")
        self.assertEqual(self.site.bandeau_hauteur, 150)
        self.assertEqual(self.site.logo, self.image)
        self.assertEqual(self.site.bandeau, self.image)


    def test_string_repr(self):
        self.assertEqual(
            str(self.site),
            "<Site page_background: #FFFFFF, page_foreground: #111111, text_title: #222222, police: Bookman>",
        )


    def test_site_update(self):
        self.site.page_background = "#000000"
        self.site.page_foreground = "#000000"
        self.site.police = "Alata"
        self.site.bandeau_hauteur = 100
        self.site.save()

        update_site = Site.objects.get(id=self.site.id)
        self.assertEqual(update_site.page_background, "#000000")
        self.assertEqual(update_site.page_foreground, "#000000")
        self.assertEqual(update_site.police, "Alata")
        self.assertEqual(update_site.bandeau_hauteur, 100)


    def test_site_delete(self):
        self.site.delete()
        self.assertEqual(Site.objects.count(), 0)
