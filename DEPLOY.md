# Backend (Django API) — serverga chiqarish

Uch qism alohida deploy qilinadi, tartib: **1. backend → 2. frontend → 3. bot**.
Hammasi bitta serverda umumiy `mentadbirkor` Docker tarmog‘i orqali bog‘lanadi.

## Eng oson yo‘l — bitta skript

Uchala repo klonlangach, `server-setup.sh` hammasini o‘zi qiladi (Docker, kalitlar, uchala `.env`, ishga tushirish):

```bash
mkdir -p /opt/mentadbirkor && cd /opt/mentadbirkor
git clone https://github.com/Nodirbek2000-tat/samarkand_git-.git backend
git clone https://github.com/Nodirbek2000-tat/samarkand_next_git-.git frontend
git clone https://github.com/Nodirbek2000-tat/samarkand_bot_git.git bot
bash backend/server-setup.sh
```

Hozircha domen yo‘q — sayt `http://173.249.39.129` da ochiladi. Quyida — qo‘lda bajarish tartibi.

## 0. Bir martalik tayyorlov (server, faqat birinchi marta)

```bash
curl -fsSL https://get.docker.com | sh
docker network create mentadbirkor
docker volume create mentadbirkor_media
docker volume create mentadbirkor_static
```

## 1. O‘rnatish

```bash
git clone https://github.com/Nodirbek2000-tat/samarkand_git-.git /opt/mentadbirkor/backend
cd /opt/mentadbirkor/backend
cp server.env.example .env
nano .env        # DJANGO_SECRET_KEY, POSTGRES_PASSWORD, DJANGO_ADMIN_PASSWORD, ikkita umumiy kalit
docker compose up -d --build
```

Birinchi ishga tushishda: migratsiyalar, statik fayllar, bo‘sh bazaga o‘zbekcha boshlang‘ich kontent
va administrator (`DJANGO_ADMIN_USERNAME` / `DJANGO_ADMIN_PASSWORD`).

## 2. Tekshirish va loglar

```bash
docker compose ps
docker compose logs -f backend
```

## 3. O‘zingizni admin qilish (Telegram hisobini)

Avval botda telefon raqamingizni yuboring, keyin:

```bash
docker compose exec backend python manage.py set_role @telegram_username admin
```

## 4. Yangilash

```bash
cd /opt/mentadbirkor/backend
git pull
docker compose up -d --build
```

## 5. Zaxira nusxa

```bash
docker compose exec -T db pg_dump -U mentadbirkor mentadbirkor | gzip > db-$(date +%F).sql.gz
docker run --rm -v mentadbirkor_media:/m -v "$PWD":/b alpine tar czf /b/media-$(date +%F).tgz -C /m .
```
