"""Kengash a’zolari alifbo tartibida; Boshqaruvda rais birinchi, qolganlar alifbo tartibida."""

from django.db import migrations


def forwards(apps, schema_editor):
    BoardMember = apps.get_model("council", "BoardMember")
    BoardMember.objects.update(order=1)
    BoardMember.objects.filter(role="chairman").update(order=0)


class Migration(migrations.Migration):

    dependencies = [("council", "0004_board_order_ibragimov_second")]

    operations = [
        migrations.AlterModelOptions(
            name="councilmember",
            options={"ordering": ["full_name"], "verbose_name": "Kengash a’zosi", "verbose_name_plural": "Kengash a’zolari"},
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
