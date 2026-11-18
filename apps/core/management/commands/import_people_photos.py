"""
Puts people's photos in place from a folder of files named after them (idempotent — safe to run again).

    python manage.py import_people_photos                 # apps/core/seed/people_photos
    python manage.py import_people_photos /path/to/folder --replace

A file "Ibragimov Nozir.jpg" goes to every person whose name has those words — a council member, the same person
on the Board and among the recognised. Each photo is cropped to the site's 4:5 frame so that every portrait looks
alike: the head is found against the studio background (white or grey), centred, given the same room above it and,
in a waist-up or wide shot, brought closer until it fills the frame like the others. Then it is scaled down and
stored as WebP. People who already have a photo are skipped unless --replace is given. A file that matches nobody,
or two different people, is reported and skipped.
"""

import re
import statistics
from io import BytesIO
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

from apps.council.models import BoardMember, CouncilMember, Leader, Recognition

DEFAULT_DIR = Path(__file__).resolve().parents[2] / "seed" / "people_photos"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
MODELS = (CouncilMember, BoardMember, Leader, Recognition)

FRAME = 4 / 5  # width / height, as on the site's cards and profile pages
MAX_SIZE = (960, 1200)
# the top of the head sits this far below the frame's top edge (share of the frame height), in every photo alike
HEAD_ROOM = 0.07
# a passport-style portrait has the head about half the frame wide; a smaller head is brought up to this
HEAD_SHARE = 0.52
MIN_HEAD_SHARE = 0.46
# coming closer keeps at least this share of the photo's width
MAX_ZOOM = 0.7


def words(name: str) -> list[str]:
    """«O‘roqov Haydar» and "Oroqov haydar" give the same words."""
    return re.sub(r"[‘’'`ʻʼ]", "", name).lower().split()


def matches(file_words: list[str], full_name: str) -> bool:
    name_words = words(full_name)
    return all(any(n.startswith(w) for n in name_words) for w in file_words)


def head_box(im: Image.Image) -> tuple[int, int, int]:
    """Top of the hair and the head's left and right edge, found against the studio background.

    The background is whatever colour the top edge and the upper sides have (white or grey); the head is the first
    thing that differs from it, and its width is the widest part of the next short stretch down (forehead and temples — not yet the shoulders)."""
    sw = 128
    sh = max(1, round(sw * im.height / im.width))
    small = im.convert("L").resize((sw, sh))
    px = small.load()
    edge = [px[x, 0] for x in range(sw)] + [px[0, y] for y in range(sh // 3)] + [px[sw - 1, y] for y in range(sh // 3)]
    bg = statistics.median(edge)
    rows = [[x for x in range(sw) if abs(px[x, y] - bg) > 28] for y in range(sh)]
    y0 = next((y for y, r in enumerate(rows) if len(r) > 2), None)
    if y0 is None:
        return 0, 0, im.width
    spans = [(r[0], r[-1]) for r in rows[y0 : y0 + round(0.25 * sw)] if len(r) > 2]
    x0, x1 = max(spans, key=lambda s: s[1] - s[0])
    scale = im.width / sw
    return round(y0 * im.height / sh), round(x0 * scale), round((x1 + 1) * scale)


def portrait(path: Path) -> bytes:
    with Image.open(path) as src:
        im = ImageOps.exif_transpose(src).convert("RGB")
    w, h = im.size
    y0, hx0, hx1 = head_box(im)
    head_w, centre = hx1 - hx0, (hx0 + hx1) / 2

    win_w = min(w, h * FRAME)  # the largest 4:5 window the photo has
    if head_w < MIN_HEAD_SHARE * win_w:  # waist-up or wide shot: come closer — but not so close that the photo
        win_w = max(head_w / HEAD_SHARE, MAX_ZOOM * win_w)  # turns blurry or loses what it shows (medals, badge)
    win_h = win_w / FRAME
    top = y0 - HEAD_ROOM * win_h
    if top + win_h > h:  # not enough photo below: shrink the window to end at the bottom edge
        win_h = (h - max(top, 0)) if top > 0 else h
        win_w = win_h * FRAME
    top = min(max(0, top), h - win_h)
    left = min(max(0, centre - win_w / 2), w - win_w)
    im = im.crop((round(left), round(top), round(left + win_w), round(top + win_h)))
    im.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
    out = BytesIO()
    im.save(out, "WEBP", quality=86, method=6)
    return out.getvalue()


class Command(BaseCommand):
    help = "Odamlarning suratlarini papkadan joyiga qo‘yadi (fayl nomi — familiya va ism)."

    def add_arguments(self, parser):
        parser.add_argument("folder", nargs="?", default=str(DEFAULT_DIR))
        parser.add_argument("--replace", action="store_true", help="surati bor odamlarnikini ham almashtirish")

    def handle(self, folder, replace, **options):
        root = Path(folder)
        if not root.is_dir():
            raise CommandError(f"Papka topilmadi: {root}")
        files = sorted(p for p in root.iterdir() if p.suffix.lower() in EXTENSIONS)
        if not files:
            self.stdout.write("Papkada rasm yo‘q.")
            return

        placed = skipped = 0
        for path in files:
            file_words = words(path.stem)
            found = []
            for Model in MODELS:
                hits = [obj for obj in Model.objects.all() if matches(file_words, obj.full_name)]
                if len({h.full_name for h in hits}) > 1:
                    names = ", ".join(sorted({h.full_name for h in hits}))
                    self.stderr.write(f"✗ {path.name}: bir nechta odamga mos keldi ({names}) — nomini aniqroq yozing")
                    found = None
                    break
                found += hits
            if found is None:
                continue
            if not found:
                self.stderr.write(f"✗ {path.name}: hech kimga mos kelmadi")
                continue

            data = portrait(path)
            for obj in found:
                label = f"{obj._meta.verbose_name}: {obj.full_name}"
                if obj.photo and not replace:
                    self.stdout.write(f"– {label} — surati bor, o‘tkazib yuborildi (--replace)")
                    skipped += 1
                    continue
                if obj.photo:
                    obj.photo.delete(save=False)
                obj.photo.save(f"{path.stem}.webp", ContentFile(data), save=False)
                obj.save(update_fields=["photo"])
                self.stdout.write(f"✓ {label}")
                placed += 1

        self.stdout.write(self.style.SUCCESS(f"Joyiga qo‘yildi: {placed}, o‘tkazib yuborildi: {skipped}."))
