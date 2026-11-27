"""
Turns the former madeinsam.uz production package into a compact bundle for import_catalog:

    python manage.py build_catalog_bundle /path/to/catalog_production_package /path/to/bundle

Reads only the catalog tables of database.sql (categories, companies, products and their pictures) — users,
sessions and tokens are never touched. Texts are tidied up (Uzbek apostrophes, Windows line breaks, broken
links dropped) and every picture is scaled down and re-encoded as WebP, so the bundle is a fraction of the
original size. Output: <bundle>/data.json and <bundle>/img/*.webp. Needs no database.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from PIL import Image, ImageOps

TABLES = {"api_category", "api_company", "api_company_images", "api_product", "api_product_images", "api_picture"}
COPY_LINE = re.compile(r"COPY public\.(\w+) \((.*)\) FROM stdin;")
ESCAPE = re.compile(r"\\(.)")
ESCAPES = {"b": "\b", "f": "\f", "n": "\n", "r": "\r", "t": "\t", "v": "\v", "\\": "\\"}
LOGO_SIZE, PHOTO_SIZE, CATEGORY_SIZE = 600, 1400, 1600
WEBP_QUALITY = 80


def read_dump(path: Path) -> dict[str, list[dict]]:
    tables: dict[str, list[dict]] = {}
    current, cols = None, []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if current is None:
                m = COPY_LINE.match(line)
                if m and m.group(1) in TABLES:
                    current, cols = m.group(1), [c.strip().strip('"') for c in m.group(2).split(",")]
                    tables[current] = []
                continue
            row = line.rstrip("\n")
            if row == "\\.":
                current = None
                continue
            values = [None if v == "\\N" else ESCAPE.sub(lambda m: ESCAPES.get(m.group(1), m.group(1)), v) for v in row.split("\t")]
            tables[current].append(dict(zip(cols, values)))
    return tables


def uz_text(value: str | None) -> str:
    """Windows line breaks and the various Uzbek apostrophes made consistent: o‘, g‘ and the tutuq ’."""
    text = (value or "").replace("\r\n", "\n").replace("\r", "\n").replace("�", "‘").strip()
    text = re.sub(r"([oOgG])['`ʻ’‘]", r"\1‘", text)
    text = re.sub(r"(?<=\w)['`ʼ](?=\w)", "’", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def name(value: str | None) -> str:
    """Company and product names: «QUOTED NAME» instead of " QUOTED NAME ", single spaces."""
    text = uz_text(value).replace("“", '"').replace("”", '"').replace("„", '"')
    text = re.sub(r'"\s*([^"]+?)\s*"', lambda m: f"«{m.group(1)}»", text)
    # "ASL NAFISI' MCHJ — a quote opened with " but closed with an apostrophe
    text = re.sub(r"^\"([^\"'’]+)['’]", lambda m: f"«{m.group(1).strip()}»", text)
    text = re.sub(r"(?<!\d)0['’‘](?=[A-Z])", "O‘", text)  # «0’ZBEGIM» typed with a zero
    if text.count('"') == 1:  # an orphan quote left over
        text = text.replace('"', "")
    return re.sub(r"\s+", " ", text).strip()


def link(value: str | None, kind: str = "") -> str:
    value = (value or "").strip()
    if not value or value in {"-", "—", "#"}:
        return ""
    if kind == "telegram" and re.fullmatch(r"@?\w{4,}", value):
        return f"https://t.me/{value.lstrip('@')}"
    if kind == "instagram" and re.fullmatch(r"@?[\w.]{2,}", value):
        return f"https://instagram.com/{value.lstrip('@')}"
    if re.match(r"^[\w.-]+\.[a-z]{2,}(/.*)?$", value, re.I):
        value = "https://" + value
    return value if re.match(r"^https?://[^\s]+\.[^\s]+", value) else ""


def email(value: str | None) -> str:
    value = (value or "").strip()
    return value if re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", value, re.I) else ""


class Command(BaseCommand):
    help = "madeinsam.uz paketidan import_catalog uchun ixcham to‘plam (data.json + WebP rasmlar) yasaydi."

    def add_arguments(self, parser):
        parser.add_argument("package")
        parser.add_argument("out")

    def handle(self, package, out, **options):
        package, out = Path(package), Path(out)
        dump = package / "database.sql"
        if not dump.is_file():
            raise CommandError(f"database.sql topilmadi: {dump}")
        (out / "img").mkdir(parents=True, exist_ok=True)
        t = read_dump(dump)
        self.media, self.out, self.jobs = package / "media", out, {}

        pictures = {p["id"]: p["image"] for p in t["api_picture"] if p["image"]}
        gallery: dict[str, list[str]] = {}
        for row in t["api_company_images"]:
            gallery.setdefault(row["company_id"], []).append(pictures.get(row["picture_id"]))
        product_pics: dict[str, list[str]] = {}
        for row in t["api_product_images"]:
            product_pics.setdefault(row["product_id"], []).append(pictures.get(row["picture_id"]))

        categories = [
            {"id": int(c["id"]), "title": uz_text(c["title"]), "image": self.picture(c["big_image"] or c["small_image"], CATEGORY_SIZE)}
            for c in sorted(t["api_category"], key=lambda c: int(c["id"]))
        ]
        companies = [
            {
                "id": int(c["id"]),
                "title": name(c["title"]),
                "category": int(c["category_id"]),
                "logo": self.picture(c["logo"], LOGO_SIZE, keep_alpha=True),
                "description": uz_text(c["description"]),
                "address": uz_text(c["address"]),
                "phone": (c["sales_dep_number"] or "").strip(),
                "sales_manager": uz_text(c["sales_manager_name"]),
                "email": email(c["email"]),
                "website": link(c["web_site"]),
                "telegram": link(c["telegram"], "telegram"),
                "instagram": link(c["instagram"], "instagram"),
                "facebook": link(c["facebook"]),
                "youtube": link(c["youtube"]),
                "whatsapp": (c["whatsapp"] or "").strip(),
                "images": [n for n in (self.picture(p, PHOTO_SIZE) for p in gallery.get(c["id"], [])) if n],
            }
            for c in t["api_company"]
        ]
        products = []
        for p in t["api_product"]:
            title, description = name(p["name"]), uz_text(p["description"])
            products.append({
                "id": int(p["id"]),
                "company": int(p["company_id"]),
                "category": int(p["category_id"]),
                "name": title,
                "description": "" if description.replace('"', "") == title.replace("«", "").replace("»", "") else description,
                "images": [n for n in (self.picture(x, PHOTO_SIZE) for x in product_pics.get(p["id"], [])) if n],
            })

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(self.convert, self.jobs.items()))
        missing = {name for (name, _, _), ok in zip(self.jobs.values(), results) if not ok}
        strip = lambda names: [n for n in names if n not in missing]  # noqa: E731
        for c in categories:
            c["image"] = "" if c["image"] in missing else c["image"]
        for c in companies:
            c["logo"] = "" if c["logo"] in missing else c["logo"]
            c["images"] = strip(c["images"])
        for p in products:
            p["images"] = strip(p["images"])

        data = {"categories": categories, "companies": companies, "products": products}
        (out / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(
            f"{len(categories)} kategoriya, {len(companies)} korxona, {len(products)} mahsulot, "
            f"{len(results) - len(missing)} rasm. Topilmagan yoki buzuq rasm: {len(missing)}"
        ))

    def picture(self, rel: str | None, size: int, keep_alpha: bool = False) -> str:
        """Plans the conversion of one media file and returns its name in the bundle ("" if there is none)."""
        if not rel:
            return ""
        name = re.sub(r"[^\w.-]+", "_", rel.rsplit(".", 1)[0]) + ".webp"
        self.jobs.setdefault(rel, (name, size, keep_alpha))
        return name

    def convert(self, job) -> bool:
        rel, (name, size, keep_alpha) = job
        src, dst = self.media / rel, self.out / "img" / name
        if dst.is_file():
            return True
        if not src.is_file():
            return False
        try:
            with Image.open(src) as im:
                im = ImageOps.exif_transpose(im)
                im = im.convert("RGBA" if keep_alpha and im.mode in ("RGBA", "LA", "P") else "RGB")
                im.thumbnail((size, size), Image.Resampling.LANCZOS)
                im.save(dst, "WEBP", quality=WEBP_QUALITY, method=5)
            return True
        except OSError:
            return False
