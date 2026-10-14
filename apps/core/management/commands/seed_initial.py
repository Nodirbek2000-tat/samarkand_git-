"""
Loads the initial Uzbek content of the site (idempotent — safe to run again).

    python manage.py seed_initial
"""

import os
from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.content.models import News
from apps.core.models import Page, SiteSettings
from apps.core.seed import forum as forum_data
from apps.core.seed import pages as pages_data
from apps.core.seed import people as people_data
from apps.core.seed import projects as projects_data
from apps.core.text import uz_slugify
from apps.council.models import BoardMember, CouncilMember, Meeting, Recognition
from apps.forum.models import ForumEdition, Nomination, Winner
from apps.partners.models import Partner
from apps.projects.models import Project, ProjectParticipant


def aware(d: date) -> datetime:
    return timezone.make_aware(datetime(d.year, d.month, d.day, 10, 0))


class Command(BaseCommand):
    help = "Bazani boshlang‘ich o‘zbekcha kontent bilan to‘ldiradi."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true", help="Faqat baza bo‘sh bo‘lsa (birinchi deploy)")

    @transaction.atomic
    def handle(self, *args, **options):
        if options["if_empty"] and Page.objects.exists():
            self.stdout.write("Baza allaqachon to‘ldirilgan — seed o‘tkazib yuborildi.")
            return
        self.settings()
        self.pages()
        self.people()
        self.projects()
        self.forum()
        self.meetings()
        self.partners()
        self.news()
        self.admin_user()
        self.stdout.write(self.style.SUCCESS("Boshlang‘ich ma’lumotlar yuklandi."))

    # ------------------------------------------------------------------ helpers
    def log(self, label, count):
        self.stdout.write(f"  {label}: {count}")

    def settings(self):
        s = SiteSettings.load()
        s.slogan = "Tadbirkorlikni jadal rivojlantirish sari birgamiz"
        s.phone = s.phone or "+998 66 233 00 01"
        s.email = s.email or "info@yangisamarqand.uz"
        s.address = s.address or "Samarqand sh., Registon ko‘chasi, 1-uy"
        s.working_hours = s.working_hours or "Du–Ju: 9:00–18:00"
        s.catalog_url = s.catalog_url or "http://madeinsam.uz"
        s.stat_members = s.stat_members or len(people_data.COUNCIL_MEMBERS)
        s.stat_catalog = s.stat_catalog or 406
        s.stat_startups = s.stat_startups or 38
        s.stat_enterprises = s.stat_enterprises or 6000
        s.save()
        self.log("Sozlamalar", 1)

    def pages(self):
        for data in pages_data.PAGES:
            Page.objects.update_or_create(
                key=data["key"],
                defaults={**{k: v for k, v in data.items() if k != "key"}, "is_published": True},
            )
        self.log("Sahifalar", len(pages_data.PAGES))

    def people(self):
        for i, (name, position, company) in enumerate(people_data.COUNCIL_MEMBERS):
            CouncilMember.objects.update_or_create(
                slug=uz_slugify(name), defaults={"full_name": name, "position": position, "company": company, "order": i}
            )
        for i, (name, role, workplace) in enumerate(people_data.BOARD_MEMBERS):
            BoardMember.objects.update_or_create(
                slug=uz_slugify(name), defaults={"full_name": name, "role": role, "workplace": workplace, "order": i}
            )
        for i, (year, name, company, award, description) in enumerate(people_data.RECOGNITIONS):
            Recognition.objects.update_or_create(
                full_name=name,
                award=award,
                defaults={"year": year, "company": company, "description": f"<p>{description}</p>", "order": i},
            )
        self.log("Kengash a’zolari", len(people_data.COUNCIL_MEMBERS))
        self.log("Boshqaruv", len(people_data.BOARD_MEMBERS))
        self.log("E’tiroflar", len(people_data.RECOGNITIONS))

    def projects(self):
        for i, data in enumerate(projects_data.PROJECTS):
            data = dict(data)
            slug = data.pop("slug")
            started = data.pop("started_on", None)
            Project.objects.update_or_create(
                slug=slug,
                defaults={
                    **data,
                    "order": i,
                    "is_published": True,
                    "started_on": date.fromisoformat(started) if started else None,
                },
            )
        siyob = Project.objects.get(slug="siyob-canal")
        for i, (company, person) in enumerate(people_data.SIYOB_INITIATORS):
            ProjectParticipant.objects.update_or_create(
                project=siyob, company=company, defaults={"person": person, "role": "Tashabbuskor", "order": i}
            )
        self.log("Loyihalar", len(projects_data.PROJECTS))
        self.log("Siyob tashabbuskorlari", len(people_data.SIYOB_INITIATORS))

    def forum(self):
        total = 0
        for data in forum_data.EDITIONS:
            edition, _ = ForumEdition.objects.update_or_create(
                year=data["year"],
                defaults={
                    "results_year": data["results_year"],
                    "title": data["title"],
                    "dates": data["dates"],
                    "location": "Samarqand",
                    "intro": forum_data.FORUM_INTRO + data["intro"],
                    "is_published": True,
                },
            )
            edition.nominations.all().delete()
            for n, (title, winners) in enumerate(data["nominations"]):
                nomination = Nomination.objects.create(edition=edition, title=title, order=n)
                Winner.objects.bulk_create(
                    Winner(nomination=nomination, level=level, name=name, note=note, order=w)
                    for w, (level, name, note) in enumerate(winners)
                )
                total += len(winners)
        self.log("Forumlar", len(forum_data.EDITIONS))
        self.log("G‘oliblar", total)

    def meetings(self):
        rows = [
            (
                date(2022, 12, 17),
                "Kengash yig‘ilishi — Siyob kanali tashabbusi",
                "«Zarafshon tekstil»",
                "<p>Siyob kanali sohilini kompleks obodonlashtirish masalasi.</p>",
                "<p>Tadbirkorlar har bir ishtirokchi uchun taxminan 2 km uzunlikdagi sohil uchastkalarini "
                "obodonlashtirish tashabbusi bilan chiqdilar.</p>",
            ),
            (
                date(2025, 3, 13),
                "Kengash a’zolari yig‘ilishi",
                "",
                "",
                "<p>Mamlakatda tadbirkorlikni rivojlantirish va minglab ish o‘rinlari yaratishdagi ko‘p yillik faoliyati "
                "uchun Kengash a’zolari Sharipov Shavkat O‘ktamovich va Abdullayev Kamol Tal’atovich «Turon» xalqaro "
                "akademiyasining faxriy a’zoligiga taqdim etildi.</p>",
            ),
            (
                date(2025, 9, 29),
                "Kengash a’zolari yig‘ilishi — Ustoz va murabbiylar kuni",
                "",
                "",
                "<p>60 yoshdan oshgan Kengash a’zolari Ustoz va murabbiylar kuni munosabati bilan esdalik plaketkalari "
                "bilan taqdirlandi. Sovg‘alarni viloyat hokimi A.M. Boboyev topshirdi.</p>",
            ),
        ]
        for d, title, host, agenda, outcome in rows:
            Meeting.objects.update_or_create(
                date=d,
                title=title,
                defaults={"host_company": host, "agenda": agenda, "outcome": outcome, "is_published": True},
            )
        self.log("Yig‘ilishlar", len(rows))

    def partners(self):
        rows = [
            (
                "O‘zbekiston Savdo-sanoat palatasi Samarqand viloyati boshqarmasi",
                "HR-mutaxassislar klubi hamkori: kadrlar tayyorlash va ishga joylashtirish masalalari.",
            ),
            ("O‘zbekiston Buxgalterlar federatsiyasi", "Buxgalterlar, auditorlar va soliq maslahatchilari klubi hamkori."),
            ("Milliy buxgalterlar va auditorlar assotsiatsiyasi", "Buxgalterlar, auditorlar va soliq maslahatchilari klubi hamkori."),
        ]
        for i, (name, description) in enumerate(rows):
            Partner.objects.update_or_create(
                name=name, defaults={"kind": "domestic", "description": description, "order": i, "is_published": True}
            )
        self.log("Hamkorlar", len(rows))

    def news(self):
        honorees = "".join(f"<li>{n}</li>" for n in people_data.TEACHERS_DAY_HONOREES)
        rows = [
            (
                "kengash-azolari-ustoz-va-murabbiylar-kuni",
                "Kengash a’zolari Ustoz va murabbiylar kuni munosabati bilan taqdirlandi",
                "council",
                date(2025, 9, 29),
                "60 yoshdan oshgan Kengash a’zolariga esdalik plaketkalarini viloyat hokimi A.M. Boboyev topshirdi.",
                "<p>2025-yil 29-sentabrda bo‘lib o‘tgan Kengash a’zolari yig‘ilishida mamlakatda tadbirkorlikni "
                "rivojlantirish bo‘yicha ko‘p yillik faoliyati uchun 60 yoshdan oshgan Kengash a’zolari Ustoz va "
                f"murabbiylar kuni munosabati bilan esdalik plaketkalari bilan taqdirlandi:</p><ol>{honorees}</ol>"
                "<p>Sovg‘alarni viloyat hokimi A.M. Boboyev topshirdi.</p>",
            ),
            (
                "kengash-azolari-davlat-mukofotlari-2025",
                "Kengash a’zolari davlat mukofotlari bilan taqdirlandi",
                "council",
                date(2025, 8, 21),
                "Prezidentning 2025-yil 21-avgustdagi farmoni bilan viloyat tadbirkorlari faxriy unvon, orden va "
                "medallar bilan taqdirlandi.",
                "<p>O‘zbekiston Respublikasi Prezidentining 2025-yil 21-avgustdagi farmoni bilan mamlakatning iqtisodiy "
                "qudrati va eksport salohiyatini oshirishdagi salmoqli yutuqlari uchun quyidagi tadbirkorlar "
                "taqdirlandi:</p><ul>"
                "<li>«O‘zbekiston Respublikasida xizmat ko‘rsatgan tadbirkor» faxriy unvoni — Abdullayev Kamol "
                "Tal’atovich («Sam Antep Gilam» MChJ) va Saidmurodov O‘ktam Saidmurodovich («Stekloplastik» MChJ);</li>"
                "<li>«Do‘stlik» ordeni — To‘rayev Zafar Suyunovich («SXF Big Stroy Building» MChJ) va Ergashev Shuhrat "
                "Sharipovich («Samarkand Garden Plast» MChJ);</li>"
                "<li>«Shuhrat» medali — Komilov Nasimjon Qobiljonovich («STD Health Med» MChJ).</li></ul>",
            ),
            (
                "sanoatchilar-forumi-2025-goliblari",
                "Sanoatchilar forumi — 2025: g‘oliblar aniqlandi",
                "forum",
                date(2025, 4, 18),
                "2024-yil sanoat rivoji yakunlari bo‘yicha to‘rt nominatsiyada eng namunali korxonalar taqdirlandi.",
                "<p>2025-yil 17–18-aprel kunlari Samarqand viloyati sanoatchilar forumi bo‘lib o‘tdi. 2024-yil yakunlari "
                "bo‘yicha g‘oliblar:</p><ul>"
                "<li>Sanoat kooperatsiyasi — «SAM FERRE» MChJ (Urgut tumani);</li>"
                "<li>Ishlab chiqarishni lokalizatsiya qilish — O‘zbekiston-Xitoy «AZIA METALL PROF» QK MChJ "
                "(Samarqand shahri);</li>"
                "<li>Sanoat mahsulotlari eksporti — «NAVOBOD NASLLI PARRANDA» fermer xo‘jaligi (Samarqand tumani);</li>"
                "<li>Eng namunali brend — «AGROMIR» QKning BLISS, MEVA JUICE, MARINELLE savdo belgilari.</li></ul>",
            ),
        ]
        for slug, title, category, d, excerpt, body in rows:
            News.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "category": category,
                    "excerpt": excerpt,
                    "body": body,
                    "is_published": True,
                    "published_at": aware(d),
                },
            )
        self.log("Yangiliklar", len(rows))

    def admin_user(self):
        username = os.environ.get("DJANGO_ADMIN_USERNAME")
        password = os.environ.get("DJANGO_ADMIN_PASSWORD")
        if not (username and password):
            self.stdout.write("  Admin: DJANGO_ADMIN_USERNAME / DJANGO_ADMIN_PASSWORD .env da yo‘q — o‘tkazib yuborildi")
            return
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username, defaults={"is_staff": True, "is_superuser": True})
        if created:
            user.set_password(password)
            user.first_name = "Bosh"
            user.last_name = "administrator"
            user.save()
        self.log("Admin", "yaratildi" if created else "mavjud")
