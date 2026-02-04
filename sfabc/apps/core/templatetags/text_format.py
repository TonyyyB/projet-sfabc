import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


_STRONG_RE = re.compile(r"\*\*(.+?)\*\*")
_EM_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


@register.filter(name="mini_markdown")
def mini_markdown(value: str) -> str:
    """Rendu 'mini-markdown' sécurisé.

    Supporte:
    - retours à la ligne (\n) -> <br>
    - **gras** -> <strong>
    - *italique* -> <em>

    Le contenu HTML entrant est échappé (anti-XSS).
    """
    if value is None:
        return ""

    text = escape(str(value))

    # Appliquer d'abord le gras, puis l'italique.
    text = _STRONG_RE.sub(r"<strong>\1</strong>", text)
    text = _EM_RE.sub(r"<em>\1</em>", text)

    # Retours à la ligne
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\n", "<br>\n")

    return mark_safe(text)
