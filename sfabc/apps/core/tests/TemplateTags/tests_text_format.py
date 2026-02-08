from django.test import SimpleTestCase

from apps.core.templatetags.text_format import mini_markdown


class MiniMarkdownFilterTest(SimpleTestCase):
    def test_newlines_to_br(self):
        out = mini_markdown("ligne1\nligne2")
        self.assertIn("ligne1<br>\nligne2", out)

    def test_bold_and_italic(self):
        out = mini_markdown("**gras** et *italique*")
        self.assertIn("<strong>gras</strong>", out)
        self.assertIn("<em>italique</em>", out)

    def test_escapes_html(self):
        out = mini_markdown('<script>alert("x")</script>')
        self.assertIn("&lt;script&gt;", out)
        self.assertNotIn("<script>", out)
