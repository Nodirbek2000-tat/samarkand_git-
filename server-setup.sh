#!/usr/bin/env bash
# mentadbirkor — serverga birinchi o‘rnatish (va qayta ishga tushirish) bitta buyruq bilan.
#
# Uchala repo bitta papkada yonma-yon klonlangan bo‘lsin (masalan /root yoki /opt/mentadbirkor):
#   samarkand_git-  samarkand_next_git-  samarkand_bot_git     (GitHub nomlari)
#   yoki  backend  frontend  bot
# Keyin:   bash samarkand_git-/server-setup.sh
#
# Nima qiladi: Docker ni o‘rnatadi (yo‘q bo‘lsa), umumiy tarmoq va volume'larni yaratadi,
# .env fayllari yo‘q bo‘lsa — maxfiy kalitlarni yaratib uchalasini to‘ldiradi (bot tokenini so‘raydi),
# so‘ng backend → frontend → bot tartibida ishga tushiradi. Mavjud .env fayllarga tegmaydi.
set -euo pipefail

say() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
setv() { sed -i "s|^$2=.*|$2=$3|" "$1"; }   # setv FILE KEY VALUE
secret() { openssl rand -hex 32; }

# backend = shu skript turgan repo; frontend va bot — uning yonidagi papkalar
BACKEND="${BACKEND:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
PARENT="$(dirname "$BACKEND")"
sibling() { for name in "$@"; do [ -d "$PARENT/$name" ] && { echo "$PARENT/$name"; return 0; }; done; return 0; }
FRONTEND="${FRONTEND:-$(sibling samarkand_next_git- frontend samarkand_next)}"
BOT="${BOT:-$(sibling samarkand_bot_git bot samarkand_bot)}"

for pair in "frontend:$FRONTEND" "bot:$BOT"; do
  [ -n "${pair#*:}" ] || { echo "Topilmadi: ${pair%%:*} papkasi $PARENT ichida yo‘q — avval repolarni klonlang"; exit 1; }
done
echo "backend:  $BACKEND"
echo "frontend: $FRONTEND"
echo "bot:      $BOT"

# ------------------------------------------------------------------ Docker
if ! command -v docker >/dev/null 2>&1; then
  say "Docker o‘rnatilmoqda"
  curl -fsSL https://get.docker.com | sh
fi

# Next.js ni yig‘ish ~1.5 GB xotira oladi: RAM kam bo‘lsa 2 GB swap qo‘shamiz
mem_mb=$(free -m | awk '/^Mem:/ {print $2}')
if [ "$mem_mb" -lt 2500 ] && [ -z "$(swapon --show 2>/dev/null)" ]; then
  say "RAM ${mem_mb} MB — 2 GB swap qo‘shilmoqda"
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile >/dev/null && swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

say "Umumiy tarmoq va volume'lar"
docker network inspect mentadbirkor >/dev/null 2>&1 || docker network create mentadbirkor
docker volume inspect mentadbirkor_media >/dev/null 2>&1 || docker volume create mentadbirkor_media
docker volume inspect mentadbirkor_static >/dev/null 2>&1 || docker volume create mentadbirkor_static

# ------------------------------------------------------------------ .env (faqat birinchi marta)
if [ ! -f "$BACKEND/.env" ]; then
  say "Maxfiy kalitlar yaratilmoqda (.env fayllar)"
  revalidate=$(secret)
  bot_api=$(secret)
  admin_password=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-16)

  cp "$BACKEND/server.env.example" "$BACKEND/.env"
  setv "$BACKEND/.env" DJANGO_SECRET_KEY "$(secret)"
  setv "$BACKEND/.env" POSTGRES_PASSWORD "$(secret)"
  setv "$BACKEND/.env" DJANGO_ADMIN_PASSWORD "$admin_password"
  setv "$BACKEND/.env" NEXT_REVALIDATE_SECRET "$revalidate"
  setv "$BACKEND/.env" BOT_API_SECRET "$bot_api"

  if [ ! -f "$FRONTEND/.env" ]; then
    cp "$FRONTEND/server.env.example" "$FRONTEND/.env"
    setv "$FRONTEND/.env" NEXT_REVALIDATE_SECRET "$revalidate"
  fi

  if [ ! -f "$BOT/.env" ]; then
    cp "$BOT/server.env.example" "$BOT/.env"
    read -rsp "Telegram bot tokeni (@BotFather): " bot_token; echo
    read -rp  "Bot ishga tushganda xabar oladigan Telegram ID (bo‘sh qoldirsa bo‘ladi): " bot_admins
    setv "$BOT/.env" BOT_TOKEN "$bot_token"
    setv "$BOT/.env" ADMINS "$bot_admins"
    setv "$BOT/.env" BOT_API_SECRET "$bot_api"
  fi
  chmod 600 "$BACKEND/.env" "$FRONTEND/.env" "$BOT/.env"
  ADMIN_NOTE="Admin panel: login admin, parol: $admin_password  (keyin almashtiring; u $BACKEND/.env da ham bor)"
fi

# ------------------------------------------------------------------ ishga tushirish
say "1/3 Backend (Django + PostgreSQL)"
(cd "$BACKEND" && docker compose up -d --build --wait)

say "2/3 Frontend (Next.js + Nginx) — birinchi marta bir necha daqiqa"
(cd "$FRONTEND" && docker compose up -d --build)

say "3/3 Bot"
(cd "$BOT" && docker compose up -d --build)

ip=$(hostname -I | awk '{print $1}')
say "Tayyor! Sayt: http://$ip"
[ -n "${ADMIN_NOTE:-}" ] && echo "$ADMIN_NOTE"
echo "Holat:  cd $BACKEND && docker compose ps   (frontend va bot papkalarida ham)"
