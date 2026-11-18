"""Mijoz bergan matn tuzatishlari — mavjud bazalar uchun (seed faqat bo‘sh bazaga yoziladi):

* Fondning rasmiy nomi (hujjatlardagidek): «Ishbilarmonlarning «YANGI SAMARQAND» hududlarni ijtimoiy-iqtisodiy
  rivojlanishiga ko‘maklashuvchi jamoat fondi» — eski «Mintaqalarni … tadbirkorlar jamoat fondi» o‘rniga;
* «mintaqa» so‘zi hamma joyda «viloyat» (mintaqaning → viloyatning, mintaqasi → viloyati …);
* yangi shior: «Birgalikda — tadbirkorlik yuksalishi sari!»;
* «Biz haqimizda» sahifasidan «Vizyon» kartochkasi olib tashlanadi;
* «Yutuqlarni e’tirof etish» sahifasi — «Eng ilg‘orlarni e’tirof etish».

Faqat shu iboralar almashadi — admin yozgan boshqa matnga tegilmaydi. Sahifalar, loyihalar va sayt sozlamalarining
barcha matn maydonlari ko‘rib chiqiladi."""

import re

from django.db import migrations, models

# whichever apostrophe an editor typed
_Q = "[‘’'`ʻ]"
_TAIL = rf"ijtimoiy-iqtisodiy rivojlantirishga ko{_Q}maklashish bo{_Q}yicha tadbirkorlar\s+jamoat fondi"

SLOGAN = "Birgalikda — tadbirkorlik yuksalishi sari!"

PHRASES = (
    # pages: «Mintaqalarni … jamoat fondi «YANGI SAMARQAND»
    (
        re.compile(rf"«(?:Mintaqalarni|Hududlarni) {_TAIL} «YANGI SAMARQAND»"),
        "«Ishbilarmonlarning «YANGI SAMARQAND» hududlarni ijtimoiy-iqtisodiy rivojlanishiga ko‘maklashuvchi jamoat fondi»",
    ),
    # project descriptions: «Yangi Samarqand» mintaqalarni … jamoat fondi
    (
        re.compile(rf"«Yangi Samarqand» (?:mintaqalarni|hududlarni) {_TAIL}"),
        "Ishbilarmonlarning «Yangi Samarqand» hududlarni ijtimoiy-iqtisodiy rivojlanishiga ko‘maklashuvchi jamoat fondi",
    ),
    (re.compile(r"Tadbirkorlikni jadal rivojlantirish sari birgamiz[.!]?"), SLOGAN),
    (re.compile(rf"Yutuqlarni e{_Q}tirof etish"), "Eng ilg‘orlarni e’tirof etish"),
)

# mintaqa + suffix → viloyat + suffix; the possessive endings change after a consonant (mintaqasi → viloyati).
# «mintaqaviy» is left alone: «viloyatviy» is not a word, and an editor should rephrase it by hand.
_MINTAQA = re.compile(r"\b([Mm])intaqa(?!viy)(si|miz|m|ngiz|ng)?")
_AFTER_CONSONANT = {"si": "i", "miz": "imiz", "m": "im", "ngiz": "ingiz", "ng": "ing"}


def _viloyat(m):
    v = "V" if m.group(1) == "M" else "v"
    return f"{v}iloyat{_AFTER_CONSONANT.get(m.group(2) or '', '')}"


def fix(text):
    for pattern, new in PHRASES:
        text = pattern.sub(new, text)
    return _MINTAQA.sub(_viloyat, text)


def _fix_json(value):
    if isinstance(value, str):
        return fix(value)
    if isinstance(value, list):
        return [_fix_json(v) for v in value]
    if isinstance(value, dict):
        return {k: _fix_json(v) for k, v in value.items()}
    return value


def _fix_rows(Model, drop_vizyon=False):
    fields = [f for f in Model._meta.fields if isinstance(f, (models.CharField, models.TextField, models.JSONField))]
    fields = [f for f in fields if not f.choices and f.name not in ("slug", "key")]
    for obj in Model.objects.all():
        changes = {}
        for f in fields:
            old = getattr(obj, f.name)
            if old in (None, ""):
                continue
            new = _fix_json(old) if isinstance(f, models.JSONField) else fix(old)
            if drop_vizyon and f.name == "blocks" and obj.key == "about":
                new = [b for b in new if not (b.get("group") == "principles" and b.get("title") == "Vizyon")]
            if new != old:
                changes[f.name] = new
        if changes:
            Model.objects.filter(pk=obj.pk).update(**changes)


def forwards(apps, schema_editor):
    _fix_rows(apps.get_model("core", "Page"), drop_vizyon=True)
    _fix_rows(apps.get_model("core", "SiteSettings"))
    _fix_rows(apps.get_model("projects", "Project"))


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_perf_sample"),
        ("projects", "0001_initial"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
