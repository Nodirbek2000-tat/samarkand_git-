"""Text helpers: Uzbek/Cyrillic-aware slugs and safe rich-text HTML."""

import re

import nh3
from django.utils.text import slugify

_CYRILLIC = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r",
    "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sh",
    "ъ": "", "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o", "қ": "q", "ғ": "g",
    "ҳ": "h",
}
_APOSTROPHES = re.compile(r"[ʻʼ‘’'`´]")


def uz_slugify(value: str, max_length: int = 80) -> str:
    """Slug for Uzbek Latin/Cyrillic text: "Yoshlar startap‘lari" -> "yoshlar-startaplari"."""
    text = _APOSTROPHES.sub("", value.lower())
    text = "".join(_CYRILLIC.get(ch, ch) for ch in text)
    slug = slugify(text)[:max_length].strip("-")
    return slug or "item"


def unique_slug(instance, value: str, field: str = "slug", max_length: int = 80) -> str:
    base = uz_slugify(value, max_length=max_length - 6)
    model = type(instance)
    slug, n = base, 2
    while model._default_manager.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


ALLOWED_TAGS = {
    "p", "br", "hr", "h2", "h3", "h4", "strong", "b", "em", "i", "u", "s", "mark", "blockquote",
    "ul", "ol", "li", "a", "img", "figure", "figcaption", "table", "thead", "tbody", "tr", "th", "td",
    "code", "pre", "span", "sub", "sup",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target"},
    "img": {"src", "alt", "title", "width", "height"},
    "th": {"colspan", "rowspan"},
    "td": {"colspan", "rowspan"},
    "span": {"class"},
    "p": {"class"},
}


def clean_html(html: str | None) -> str:
    """Sanitise editor HTML (XSS-safe) before it is stored."""
    if not html:
        return ""
    return nh3.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes={"http", "https", "mailto", "tel"},
        link_rel="noopener noreferrer",
    ).strip()


def plain_to_html(text: str) -> str:
    """Turn plain paragraphs (blank-line separated) into <p> blocks."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text.strip()) if b.strip()]
    out = []
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if all(ln.startswith(("•", "-", "–")) for ln in lines):
            items = "".join(f"<li>{ln.lstrip('•-– ').strip()}</li>" for ln in lines)
            out.append(f"<ul>{items}</ul>")
        else:
            out.append("<p>" + "<br>".join(lines) + "</p>")
    return "\n".join(out)
