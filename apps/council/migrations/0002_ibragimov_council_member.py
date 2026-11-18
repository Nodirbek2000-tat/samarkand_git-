"""Ibragimov Nozir Aliyevich — Boshqaruv raisi o‘rinbosari, u ham Kengash a’zosi: saytda ikkala ro‘yxatda chiqadi
(boshqa o‘rinbosarlar kabi). Mavjud bazalarga qo‘shiladi; ro‘yxat kirill alifbosi tartibida, shuning uchun
Karimovdan oldin turadi. Boshqaruvdagi surati bo‘lsa, shu yerga ham o‘tadi."""

from django.db import migrations
from django.db.models import F

NAME = "Ibragimov Nozir Aliyevich"
SLUG = "ibragimov-nozir-aliyevich"


def forwards(apps, schema_editor):
    CouncilMember = apps.get_model("council", "CouncilMember")
    if CouncilMember.objects.filter(full_name=NAME).exists():
        return
    after = CouncilMember.objects.filter(full_name__startswith="Karimov Ravshan").first()
    if after:
        order = after.order
        CouncilMember.objects.filter(order__gte=order).update(order=F("order") + 1)
    else:
        order = CouncilMember.objects.count()
    CouncilMember.objects.create(
        full_name=NAME,
        slug=SLUG,
        position="Dual ta’lim markazi direktori",
        company="Samarqand xalqaro texnologiya universiteti",
        order=order,
    )


def backwards(apps, schema_editor):
    apps.get_model("council", "CouncilMember").objects.filter(slug=SLUG).delete()


class Migration(migrations.Migration):

    dependencies = [("council", "0001_initial")]

    operations = [migrations.RunPython(forwards, backwards)]
