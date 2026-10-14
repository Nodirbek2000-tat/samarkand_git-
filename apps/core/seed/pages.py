"""Editable content pages (key -> data). Admins can rewrite everything later."""

from .people import TEACHERS_DAY_HONOREES

ABOUT_INTRO = (
    "«Mintaqalarni ijtimoiy-iqtisodiy rivojlantirishga ko‘maklashish bo‘yicha tadbirkorlar jamoat fondi «YANGI SAMARQAND» "
    "nodavlat notijorat tashkiloti 2021-yil 1-dekabrda Samarqand viloyati Adliya boshqarmasi tomonidan 295-raqam bilan "
    "ro‘yxatga olingan. Tadbirkorlar jamoat maslahat kengashi Fondning Vasiylik kengashi funksiyalari, huquqlari va "
    "vakolatlariga tenglashtirilgan."
)

PAGES = [
    {
        "key": "about",
        "section": "about",
        "title": "Biz haqimizda",
        "subtitle": "Tadbirkorlikni jadal rivojlantirish sari birgamiz.",
        "body": f"<p>{ABOUT_INTRO}</p>",
        "blocks": [
            {"group": "principles", "title": "Shior", "body": "Tadbirkorlikni jadal rivojlantirish sari birgamiz."},
            {
                "group": "principles",
                "title": "Missiya",
                "body": "Mintaqaning biznes va investitsiya muhitini yaxshilashga, jamiyatda tadbirkorlar nufuzini "
                "mustahkamlashga hamda korxonalarning barqaror rivojlanishiga hissa qo‘shish.",
            },
            {
                "group": "principles",
                "title": "Maqsadlar",
                "body": "Viloyat korxonalari o‘rtasida kooperatsion aloqalarni rivojlantirish, tadbirkorlik "
                "subyektlarida zamonaviy boshqaruv tamoyillarini joriy etish, davlat muassasalari tomonidan biznesga "
                "sifatli xizmat ko‘rsatilishiga erishish va tadbirkorlarning qonuniy huquqlarini himoya qilish.",
            },
            {
                "group": "principles",
                "title": "Vizyon",
                "body": "Tadbirkorlik uchun yaratilgan sharoitlardan samarali foydalanishda davlat boshqaruv organlari "
                "bilan hamkorlik qilish va biznes rivojiga ko‘maklashish.",
            },
            {
                "group": "values",
                "title": "Shaffoflik va hisobdorlik",
                "body": "Barcha tadbirlar hamjamiyatga e’lon qilinadi; a’zolar ularning natijadorligi va moliyaviy "
                "resurslardan foydalanish haqida muntazam xabardor qilinadi.",
            },
            {
                "group": "values",
                "title": "Ijtimoiy mas’uliyat va jamiyatdagi faollik",
                "body": "Tadbirkor mintaqaning ijtimoiy hayotida faol ishtirok etadi — o‘zi tarbiyalangan bog‘cha, "
                "o‘qigan maktab va oliy o‘quv yurti, yashaydigan mahalladagi ijobiy o‘zgarishlarni tashkil etishda.",
            },
            {
                "group": "values",
                "title": "Ta’lim, sog‘liqni saqlash va kambag‘allikni qisqartirishni qo‘llab-quvvatlash",
                "body": "Tadbirkorlarning ta’lim, sog‘liqni saqlash va kambag‘allikni qisqartirish sohalariga homiylik "
                "hissasini ommalashtirish, samarali ijtimoiy loyihalar va ijobiy tajribani tarqatish.",
            },
            {
                "group": "values",
                "title": "Innovatsiyalar va yoshlar startaplarini qo‘llab-quvvatlash",
                "body": "Innovatsiyalar, samarali g‘oyalar va yoshlar startaplarini aniqlash, ularni "
                "tijoratlashtirishgacha yetkazish, moliyalashtirish manbalarini topish.",
            },
            {
                "group": "values",
                "title": "Kichik, individual va yoshlar tadbirkorligini qo‘llab-quvvatlash",
                "body": "Kichik, individual va yoshlar tadbirkorligini rivojlantirishga ko‘maklashish, hamkorlik, "
                "homiylik va «Ustoz-shogird» mentorlik tamoyillarini qo‘llash.",
            },
            {
                "group": "values",
                "title": "Hamkorlik, birdamlik va qo‘shma loyihalar",
                "body": "O‘z ehtiyojlari uchun mahalliy korxonalar mahsulotini xarid qilish va xizmatlaridan foydalanish, "
                "istiqbolli loyihalarda birgalikda ishtirok etish, tadbirkorlik muammolarini hal qilishda kollegial "
                "ishlash.",
            },
            {
                "group": "values",
                "title": "Salmoqli hissa qo‘shgan tadbirkorlarni e’tirof etish",
                "body": "Minglab ish o‘rinlari yaratgan tadbirkorlar, faol jamoat arboblari, soha yetakchilari, zamonaviy "
                "boshqaruv tizimlari, axborot texnologiyalari va sun’iy intellekt elementlarini joriy etgan "
                "tadbirkorlarni e’tirof etish va rag‘batlantirish.",
            },
        ],
    },
    {
        "key": "about-history",
        "section": "about",
        "title": "Tashkil topish tarixi",
        "subtitle": "2021-yil 1-dekabrdan buyon — tadbirkorlar va hokimiyat o‘rtasidagi muloqot maydoni.",
        "body": f"<p>{ABOUT_INTRO}</p>"
        "<p>Kengash viloyatning yetakchi tadbirkorlarini birlashtiradi va hokimiyat bilan muntazam, natijaga "
        "yo‘naltirilgan muloqotni yo‘lga qo‘yadi: a’zolar yig‘ilishlari viloyat hokimi ishtirokida o‘tadi, bildirilgan "
        "muammolar bayonnomaga kiritiladi va ijrosi nazorat qilinadi.</p>",
        "blocks": [
            {"group": "timeline", "title": "2021", "body": "1-dekabr — «Yangi Samarqand» jamoat fondi Samarqand viloyati Adliya boshqarmasida 295-raqam bilan ro‘yxatga olindi."},
            {"group": "timeline", "title": "2022", "body": "17-dekabr — «Zarafshon tekstil»da o‘tgan Kengash majlisida Siyob kanali sohilini obodonlashtirish tashabbusi ilgari surildi."},
            {"group": "timeline", "title": "2023", "body": "30–31-may — Samarqand viloyati sanoatchilar forumi ilk bor o‘tkazildi."},
            {"group": "timeline", "title": "2024", "body": "16–17-may — Sanoatchilar forumi-2024; yil davomida 30 ta yoshlar startapi 1,9 mlrd so‘mga qo‘llab-quvvatlandi."},
            {"group": "timeline", "title": "2025", "body": "17–18-aprel — Sanoatchilar forumi-2025; Kengash a’zolari davlat mukofotlari bilan taqdirlandi."},
        ],
    },
    {
        "key": "about-corporate",
        "section": "about",
        "title": "Korporativ elementlar",
        "subtitle": "Kengashning nomi, shiori va vizual uslubi.",
        "body": "<p>«Yangi Samarqand» brendi Samarqandning ming yillik me’moriy merosi va zamonaviy tadbirkorlik ruhini "
        "birlashtiradi. Logotipdagi sakkiz qirrali yulduz — Temuriylar me’morchiligidagi girih naqshining asosiy "
        "elementi bo‘lib, birdamlik, muvozanat va barcha yo‘nalishlarga ochiqlikni ifodalaydi.</p>",
        "blocks": [
            {"group": "elements", "title": "To‘liq nomi", "body": "«Mintaqalarni ijtimoiy-iqtisodiy rivojlantirishga ko‘maklashish bo‘yicha tadbirkorlar jamoat fondi «YANGI SAMARQAND»"},
            {"group": "elements", "title": "Shior", "body": "Tadbirkorlikni jadal rivojlantirish sari birgamiz."},
            {"group": "elements", "title": "Belgi", "body": "Sakkiz qirrali girih yulduzi — Registon naqshlaridan ilhomlangan."},
            {"group": "colors", "title": "Firuza", "body": "#007F78 — Samarqand gumbazlari rangi"},
            {"group": "colors", "title": "Lojuvard", "body": "#2340D4 — Registon koshinlari"},
            {"group": "colors", "title": "Oltin", "body": "#A5620B — ishonch va qadriyat"},
        ],
    },
    {
        "key": "membership",
        "section": "about",
        "title": "A’zolik shartlari",
        "subtitle": "Kengashga a’zo bo‘ling — mintaqa o‘zgarishlarining tashkilotchisiga aylaning.",
        "body": "<p>Jamoat Kengashi a’zolari (ishtirokchilari) Fond Nizomini va maqsadlarini tan oladigan, Kengash "
        "faoliyatida faol ishtirok etadigan, Nizom vazifalarini amalga oshirish uchun ixtiyoriy ravishda pul va mulkiy "
        "badallar kiritadigan mahalliy va xorijiy yuridik hamda jismoniy shaxslar bo‘lishi mumkin. Ular Kengashda "
        "muhokama qilinadigan masalalarda ovoz berish huquqiga ega.</p>"
        "<p>Ko‘rsatilgan summalardan yuqori yoki pastroq badal kiritish, shuningdek Fondning nizomiy maqsadlarini amalga "
        "oshirish uchun zarur bo‘lgan har qanday mol-mulkni kiritishga ruxsat etiladi.</p>"
        "<p>Jamoat Kengashi faoliyatida ishtirok etish — ma’naviy ozuqa; uning faoliyatini moliyalashtirishni "
        "tadbirkorlikni rivojlantirish yo‘lidagi xarajatlar sifatida ko‘rish lozim.</p>",
        "blocks": [
            {"group": "tiers", "title": "Yakka tartibdagi tadbirkorlar va jismoniy shaxslar", "body": "5,0 mln so‘m"},
            {"group": "tiers", "title": "Kichik korxonalar (yillik realizatsiya 10,0 mlrd so‘mgacha)", "body": "10,0 mln so‘m"},
            {"group": "tiers", "title": "O‘rta korxonalar (yillik realizatsiya 10,0 mlrd so‘mdan ortiq)", "body": "25,0 mln so‘m"},
            {"group": "tiers", "title": "Yirik korxonalar (yillik realizatsiya 100,0 mlrd so‘mdan ortiq)", "body": "50,0 mln so‘m"},
            {"group": "benefits", "title": "Mintaqaning nufuzli tadbirkorlar hamjamiyati tarkibida bo‘lishdan faxrlanish", "body": ""},
            {"group": "benefits", "title": "Ijtimoiy-iqtisodiy islohotlar va ijobiy o‘zgarishlarning ishtirokchisi bo‘lish", "body": ""},
            {"group": "benefits", "title": "Gaz, elektr energiya, suv ta’minoti, kadastr va boshqa xizmatlarni, shuningdek ta’lim, sog‘liqni saqlash va ijtimoiy ta’minotni yaxshilash bo‘yicha takliflar bilan chiqish", "body": ""},
            {"group": "benefits", "title": "Kengash bilan birga o‘zgarishlar tashkilotchisi bo‘lish, viloyatning ilg‘or tadbirkorlari safida turish", "body": ""},
            {"group": "benefits", "title": "Kengash majlislarida o‘z biznesingiz muammolarini ko‘tarish va yechim taklif qilish", "body": ""},
            {"group": "benefits", "title": "A’zo-tadbirkorlarning ilg‘or tajribasi bilan tanishish, yangi g‘oyalar va tajriba almashish", "body": ""},
            {"group": "benefits", "title": "Treninglar, seminarlar, xorijiy tadbirkorlar va investorlar bilan uchrashuvlarda ishtirok etish", "body": ""},
            {
                "group": "honorary",
                "title": "Faxriy a’zolik",
                "body": "Mamlakat va mintaqaning ijtimoiy-iqtisodiy rivojiga katta hissa qo‘shgan, faol hayot tarzini olib "
                "borayotgan pensiya yoshidagi fuqarolar hech qanday badal kiritmasdan Jamoat fondi a’zosi bo‘lishlari mumkin.",
            },
        ],
    },
    {
        "key": "meetings",
        "section": "council",
        "title": "Kengash a’zolari yig‘ilishlari",
        "subtitle": "Yig‘ilishlar — Kengash ishining asosiy shakllaridan biri.",
        "body": "<p>Yig‘ilishlar mahsulotining bozor ulushi, ishlab chiqarish ko‘lami, assortimenti, eksporti hamda samarali "
        "korporativ boshqaruvi bilan ajralib turadigan a’zo-kompaniyalardan birining hududida chaqiriladi.</p>"
        "<p>Yig‘ilishlarga Kengash a’zolaridan tashqari, faoliyati bo‘yicha a’zolarda savollar bo‘lishi mumkin bo‘lgan "
        "korxona va muassasalar rahbarlari taklif etiladi. Soliq boshqarmasi, elektr tarmoqlari, gaz ta’minoti, "
        "suvoqova va kadastr xizmati rahbarlari — yig‘ilishlarning doimiy ishtirokchilari. Taklif etiladigan "
        "muassasalar ro‘yxati har bir yig‘ilishning kun tartibiga bog‘liq.</p>"
        "<p>Yig‘ilishda viloyat hokimi ishtirok etadi. Yig‘ilish boshlanishidan oldin ishtirokchilar mezbon kompaniyaning "
        "ishlab chiqarish faoliyati bilan tanishadilar.</p>"
        "<p>Yig‘ilishni Kengash Boshqaruvi raisi H.M. O‘roqov tasdiqlangan va barcha a’zolarga yuborilgan kun tartibi "
        "asosida olib boradi. Kompaniyalar faoliyatini va viloyatdagi biznes muhitini yaxshilash bo‘yicha bildirilgan "
        "muammo va takliflar yuzasidan hokim mas’ul rahbarlarga topshiriq beradi; ular yig‘ilish bayonnomasiga "
        "kiritiladi va ijrosi nazoratga olinadi.</p>",
        "blocks": [],
    },
    {
        "key": "recognition",
        "section": "council",
        "title": "Yutuqlarni e’tirof etish",
        "subtitle": "Xizmat ko‘rsatgan, o‘zini ko‘rsatgan tadbirkorlarni jamoatchilik tomonidan e’tirof etish loyihasi.",
        "body": "<p>Tadbirkorlarning xizmatlarini e’tirof etish — mamlakatda tadbirkorlik nufuzini oshirish, tadbirkorni "
        "biznesdagi yangi yutuqlarga undash, xayriya va ezgu ishlar ko‘lamini kengaytirish yo‘nalishlaridan biri.</p>"
        "<p>Kengash Boshqaruvi biznesni kengaytirish va yangi ish o‘rinlari yaratish, sog‘liqni saqlash, ta’lim, "
        "muhtojlarga yordam sohalarida xayriya aksiyalarini amalga oshirgan tadbirkorlarning xizmatlarini qayd etish "
        "imkoniyatlarini doimo izlaydi.</p>"
        "<h2>Ustoz va murabbiylar kuni munosabati bilan tabriklar</h2>"
        "<p>2025-yil 29-sentabrdagi Kengash a’zolari yig‘ilishida mamlakatda tadbirkorlikni rivojlantirish bo‘yicha ko‘p "
        "yillik faoliyati uchun 60 yoshdan oshgan Kengash a’zolari Ustoz va murabbiylar kuni munosabati bilan esdalik "
        "plaketkalari bilan taqdirlandi:</p>"
        "<ol>" + "".join(f"<li>{name}</li>" for name in TEACHERS_DAY_HONOREES) + "</ol>"
        "<p>Sovg‘alarni viloyat hokimi A.M. Boboyev topshirdi.</p>",
        "blocks": [],
    },
    {
        "key": "projects-completed",
        "section": "projects",
        "title": "Amalga oshirilgan loyihalar",
        "subtitle": "Kengash Boshqaruvi va a’zolari tashabbusi bilan boshlangan va to‘liq amalga oshirilgan loyihalar.",
        "body": "<p>Jamoat maslahat kengashining amalga oshirilgan loyihalari — Kengash Boshqaruvi va/yoki a’zolari tashabbusi "
        "bilan boshlangan va to‘liq yakunlangan loyihalardir.</p>"
        "<p>Bu bo‘limda Kengashning moliyaviy ko‘magi, a’zolarining shaxsiy yordami yoki tadbirkorlarning o‘z hissalari "
        "hisobidan birgalikdagi sa’y-harakatlar bilan amalga oshirilgan loyihalarni ko‘rishingiz mumkin.</p>",
        "blocks": [],
    },
    {
        "key": "projects-active",
        "section": "projects",
        "title": "Amaldagi loyihalar",
        "subtitle": "Kengash Boshqaruvi tashabbusi bilan boshlangan va hozir faoliyat yuritayotgan loyihalar.",
        "body": "<p>Jamoat maslahat kengashining amaldagi loyihalari — Kengash Boshqaruvi tashabbusi bilan boshlangan va real "
        "vaqtda faoliyat yuritayotgan loyihalar.</p>"
        "<p>Loyihalarning asosiy maqsadi — biznes yuritish uchun qulay muhit yaratish, tadbirkorlik rivojiga to‘sqinlik "
        "qilayotgan muammolarni hal etish yo‘llarini topish, yoshlar startaplari va olimlarning ilmiy ishlanmalarini, "
        "kichik va yoshlar tadbirkorligini qo‘llab-quvvatlash.</p>",
        "blocks": [],
    },
    {
        "key": "cooperation",
        "section": "cooperation",
        "title": "Hamkorlik",
        "subtitle": "Mahalliy va xalqaro tashkilotlar bilan birgalikda tadbirkorlik muhitini rivojlantiramiz.",
        "body": "<p>Kengash davlat organlari, ta’lim muassasalari, kasbiy uyushmalar va xalqaro tashkilotlar bilan hamkorlikda "
        "loyihalarni amalga oshiradi. Hamkorlik taklifingiz bo‘lsa — quyidagi forma orqali yuboring.</p>",
        "blocks": [],
    },
]
