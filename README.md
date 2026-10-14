# Yangi Samarqand — backend (Django + DRF)

Sayt va admin panel uchun API. Frontend: `../samarkand_next` (Next.js).

## Ishga tushirish (lokal)

```bash
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_initial      # boshlang‘ich o‘zbekcha kontent + birinchi administrator
python manage.py runserver 127.0.0.1:8000
```

`.env` faylida (gitga qo‘shilmaydi) maxfiy kalit va birinchi administrator login/paroli turadi.
Namuna: `.env.example`. Administrator parolini kirgandan so‘ng **Profil → Parolni almashtirish** orqali o‘zgartiring.

- API hujjatlari (Swagger): http://127.0.0.1:8000/api/docs
- Zaxira Django admin: http://127.0.0.1:8000/django-admin/
- Testlar: `python manage.py test apps`

## Tuzilma

| Ilova | Nima saqlaydi |
|---|---|
| `apps/core` | Sayt sozlamalari, tahrirlanadigan sahifalar (`Page`, kalit bo‘yicha), umumiy bazaviy modellar, ruxsatlar, kesh yangilash, qidiruv, dashboard, `seed_initial` |
| `apps/accounts` | Login/logout/CSRF, joriy foydalanuvchi, parol almashtirish, administratorlarni boshqarish, Telegram bot orqali ro‘yxatdan o‘tish va kirish, shaxsiy kabinet |
| `apps/content` | Yangiliklar (+ rasmlar), filmlar, e’lonlar/tadbirlar, fotohisobotlar (+ suratlar) |
| `apps/projects` | Loyihalar (+ rasmlar, hujjatlar, ishtirokchilar — masalan Siyob tashabbuskorlari) |
| `apps/council` | Kengash a’zolari, Boshqaruv, Rahbariyat, yig‘ilishlar, e’tiroflar |
| `apps/forum` | Sanoatchilar forumi: yil → nominatsiya → g‘oliblar |
| `apps/partners` | Mahalliy va xalqaro hamkorlar |
| `apps/inbox` | Murojaatlar, hamkorlik takliflari, a’zolik arizalari (ommaviy forma + admin ish jarayoni) |

## Rollar

- **Administrator** (`is_superuser`) — hamma narsa: kontent, murojaatlar, sozlamalar, xodimlar.
- **Muharrir** (`is_staff`) — faqat kontent (yangiliklar, loyihalar, Kengash, forum, sahifalar).
- **Sayt foydalanuvchisi** — Telegram bot orqali ro‘yxatdan o‘tgan tadbirkor. Panelga kira olmaydi, faqat `/kabinet`:
  murojaatlari holati, Kengash javoblari, profil. Administrator ularni «Sayt foydalanuvchilari» bo‘limida bloklay oladi.
- Saytni hamma login’siz ko‘radi va formalarni ham login’siz yuborsa bo‘ladi.

## Telegram bot (ro‘yxatdan o‘tish va kirish)

Parol yo‘q: foydalanuvchi botga telefon raqamini yuboradi (bu — ro‘yxatdan o‘tish), bot 6 xonali kod beradi,
kod saytdagi `/kirish` sahifasiga kiritiladi. Kod 5 daqiqa amal qiladi, bir marta ishlaydi, bazada faqat HMAC-xeshi saqlanadi.

**Bot — alohida loyiha:** `../samarkand_bot` (aiogram 2). Telegram token faqat o‘sha yerda turadi; Django Telegram’ga
umuman ulanmaydi. Bot Django bilan ichki API orqali gaplashadi:

| Endpoint | Vazifasi |
|---|---|
| `POST /api/bot/hello` | bot ishga tushganda o‘z username’ini aytadi (sayt `/kirish` dagi havolani shundan oladi) |
| `POST /api/bot/register` | foydalanuvchi o‘z kontaktini yubordi → ro‘yxatdan o‘tkazish + kod |
| `POST /api/bot/code` | yangi kod (404 — hali ro‘yxatdan o‘tmagan, 429 — 30 soniya kutish, 403 — bloklangan) |
| `POST /api/bot/member` | foydalanuvchi botni blokladi / qayta yoqdi |
| `GET /api/bot/outbox` | sayt yubormoqchi bo‘lgan xabarlar navbati (bu so‘rov botning «tirikman» signali ham) |
| `POST /api/bot/outbox/<id>/ack` | xabar yuborildi / xato (5 martagacha qayta uriniladi) / foydalanuvchi bloklagan |

Hammasi `X-Bot-Secret` sarlavhasi bilan himoyalangan: `.env` dagi `BOT_API_SECRET` bot `.env` idagi bilan **bir xil** bo‘lishi shart.
Kabinetdan yuborilgan murojaatga admin javob yozsa, javob kabinetda ko‘rinadi va navbat (`BotMessage`) orqali botga ketadi.
Keyinchalik boshqa xabarlarni ham (e’lonlar, eslatmalar) xuddi shu navbat orqali yuborish mumkin: `apps.accounts.telegram.notify(user, text)`.

Botni ishga tushirish — `../samarkand_bot/README.md`. Bot ishlamasa ham sayt ishlayveradi; admin panel bosh sahifasida
bot holati («Ishlayapti / To‘xtagan») va navbatdagi xabarlar soni ko‘rinadi.

## Xavfsizlik

Sessiya + CSRF (frontend `/api` ni proksi qiladi, shuning uchun bitta domen), matn muharriridan kelgan HTML `nh3` bilan tozalanadi,
fayllar turi va hajmi tekshiriladi, ommaviy formalarda honeypot va so‘rovlar limiti (soatiga 20), login uchun daqiqasiga 10 urinish.

Kontent saqlanganda Django `NEXT_REVALIDATE_URL` ga signal yuboradi — sayt sahifalari darhol yangilanadi.

## Production

Serverga chiqarish Docker Compose bilan (backend + PostgreSQL), frontend va bot alohida deploy qilinadi: `DEPLOY.md`. Backend image: `Dockerfile` (gunicorn), ishga tushishda migratsiya, `collectstatic` va
bo‘sh bazaga boshlang‘ich kontent (`seed_initial --if-empty`). Rol berish: `python manage.py set_role @username admin`.
