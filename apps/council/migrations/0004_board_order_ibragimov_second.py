"""Boshqaruvda tartib: raisdan (O‘roqov) keyin ikkinchi bo‘lib Ibragimov Nozir Aliyevich turadi,
undan keyin boshqa o‘rinbosarlar avvalgi tartibda."""

from django.db import migrations

ORDER = (
    "O‘roqov Haydar Muhammadiyevich",
    "Ibragimov Nozir Aliyevich",
    "Marupov Baxtiyor Mahmudovich",
    "Abdullayev Kamol Tal’atovich",
    "Komilov Nasimjon Qobiljonovich",
)


def forwards(apps, schema_editor):
    BoardMember = apps.get_model("council", "BoardMember")
    rest = BoardMember.objects.exclude(full_name__in=ORDER).order_by("order", "full_name")
    names = list(ORDER) + [m.full_name for m in rest]
    for i, name in enumerate(names):
        BoardMember.objects.filter(full_name=name).update(order=i)


class Migration(migrations.Migration):

    dependencies = [("council", "0003_komilov_nasimjon")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
