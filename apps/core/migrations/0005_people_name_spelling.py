"""Bir odamning ismi saytning hamma joyida bir xil yozilsin — Kengash a’zolari ro‘yxatidagidek (mijoz yuborgan
fayl nomlari bo‘yicha): Siyob kanali tashabbuskorlari, «Ustoz va murabbiylar kuni» ro‘yxati (sahifa va yangilik)."""

from django.db import migrations

NAMES = (
    ("Qayumov Akbar Qosimaliyevich", "Qayumov Akbarali Qosimaliyevich"),
    ("Toshev Muzrob", "Toshov Mizrob Mahmudovich"),
    ("Baxronov Damir Ravshanovich", "Baxranov Damir Ravshanjonovich"),
    ("Bagirov Nosir Musoyevich", "Bagirov Nosir Musayevich"),
)


def fix(text):
    for old, new in NAMES:
        text = text.replace(old, new)
    return text


def forwards(apps, schema_editor):
    targets = (
        ("projects", "ProjectParticipant", ("person",)),
        ("content", "News", ("body",)),
        ("core", "Page", ("body",)),
    )
    for app, model, fields in targets:
        Model = apps.get_model(app, model)
        for obj in Model.objects.all():
            changes = {f: fix(getattr(obj, f)) for f in fields if getattr(obj, f) and fix(getattr(obj, f)) != getattr(obj, f)}
            if changes:
                Model.objects.filter(pk=obj.pk).update(**changes)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_content_wording"),
        ("projects", "0001_initial"),
        ("content", "0002_film_video_file"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
