"""Komilov Nasimjon Qobiljonovich — mijoz tasdiqladi: ism saytning hamma joyida «Nasimjon» bo‘lsin
(Kengash, Boshqaruv, E’tirof). Havola (slug) o‘zgarmaydi, eski linklar ishlayveradi."""

import json

from django.db import migrations

OLD, NEW = "Komilov Nasim Qobiljonovich", "Komilov Nasimjon Qobiljonovich"


def forwards(apps, schema_editor):
    for model in ("CouncilMember", "BoardMember", "Leader"):
        apps.get_model("council", model).objects.filter(full_name=OLD).update(full_name=NEW)

    targets = (
        ("projects", "ProjectParticipant", ("person",)),
        ("content", "News", ("body",)),
        ("core", "Page", ("body", "blocks")),
    )
    for app, model, fields in targets:
        Model = apps.get_model(app, model)
        for obj in Model.objects.all():
            changes = {}
            for f in fields:
                value = getattr(obj, f)
                if isinstance(value, str):
                    if OLD in value:
                        changes[f] = value.replace(OLD, NEW)
                elif value:
                    raw = json.dumps(value, ensure_ascii=False)
                    if OLD in raw:
                        changes[f] = json.loads(raw.replace(OLD, NEW))
            if changes:
                Model.objects.filter(pk=obj.pk).update(**changes)


class Migration(migrations.Migration):

    dependencies = [
        ("council", "0002_ibragimov_council_member"),
        ("core", "0005_people_name_spelling"),
        ("projects", "0001_initial"),
        ("content", "0002_film_video_file"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
