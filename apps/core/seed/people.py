"""Council people — transliterated to Uzbek Latin from the official list (18.05.2026)."""

FOUNDER = "Ta’sischi"
DIRECTOR = "Direktor"
HEAD = "Rahbar"

# (full name, position, company)
COUNCIL_MEMBERS = [
    ("Abdullayev Kamol Tal’atovich", FOUNDER, "«SAG» kompaniyalar guruhi"),
    ("Azizov Suhrob Hamidovich", DIRECTOR, "«GULOBOD YUG‘OCH» MChJ"),
    ("Azimov Sohib Asatovich", FOUNDER, "«IDEAL» kompaniyalar guruhi"),
    ("Axmedov Akmal Shomurodovich", FOUNDER, "«FERRE» kompaniyalar guruhi"),
    ("Bagirov Nosir Musayevich", DIRECTOR, "«CHAYKA STROY SERVIS» MChJ"),
    ("Baxranov Damir Ravshanjonovich", DIRECTOR, "«ASIA METALL PROF» MChJ"),
    ("Beknazarov Baxtiyor Barakayevich", DIRECTOR, "«SAMARKAND GOLDEN CHEAKPEAS» MChJ"),
    ("Jalolov Shavkat Amonovich", FOUNDER, "«AGROMIR» kompaniyalar guruhi"),
    ("Jahongirov Tolib Muzaffarovich", DIRECTOR, "«SHAXREZADA SAM STAR TUR» MChJ"),
    ("Ziyoyev Fayzullo Ziyoyevich", DIRECTOR, "«SAMARQAND KONSERVA» MChJ"),
    ("Karimov Ravshan Murodovich", FOUNDER, "«METIN» kompaniyalar guruhi"),
    ("Komilov Nasim Qobiljonovich", FOUNDER, "«MEROS PHARM» kompaniyalar guruhi"),
    ("Qo‘chqorova Gulbeka Allamuratovna", HEAD, "«BEKA CHAROS» XK"),
    ("Marupov Baxtiyor Mahmudovich", FOUNDER, "«SIYOB» kompaniyalar guruhi"),
    ("Mirboboyev Shahob Asatilla o‘g‘li", DIRECTOR, "«URGUT MIKRO METALL» MChJ"),
    ("Munisov Abduaziz Abduboriyevich", FOUNDER, "«TESPACK» kompaniyalar guruhi"),
    ("Niyozova Mar’yam Qodirovna", HEAD, "«KUMUSH TOLA» XK"),
    ("Norboyev Anvar Ochilovich", DIRECTOR, "«KATTAQO‘RG‘ON ELEKTROTEXNIKA ZAVODI» MChJ"),
    ("Rahmatov Farhod", DIRECTOR, "«GULOBOD MEBEL» MChJ"),
    ("Rahimov Po‘lat Rahimovich", FOUNDER, "«REGAL» kompaniyalar guruhi"),
    ("Saidmurodov O‘ktam Saidmurodovich", FOUNDER, "«STEKLOPLASTIK» MChJ"),
    ("Salimova Sayyora Tojiyevna", FOUNDER, "«EKO PLANETA» kompaniyalar guruhi"),
    ("To‘rayev Zafar Suyunovich", FOUNDER, "«SXF» kompaniyalar guruhi"),
    ("Fayzullayev Suhrob Abdullayevich", DIRECTOR, "«STAR LINGER» MChJ"),
    ("Xoliqov Narziqul Axtamovich", DIRECTOR, "«XAMIDOV MURODJON» MChJ"),
    ("Sharipov Shavkat O‘ktamovich", FOUNDER, "«SHARQ SANOAT» konserni"),
    ("Shodmonqulov Baxtiyor G‘ulomovich", FOUNDER, "«SOF» kompaniyalar guruhi"),
    ("Shukurullayev Dilshod Dalerovich", FOUNDER, "«ZARMED» kompaniyalar guruhi"),
    ("O‘roqov Haydar Muhammadiyevich", FOUNDER, "«NAVOBOD NASLLI PARRANDA» kompaniyalar guruhi"),
    ("Qayumov Akbarali Qosimaliyevich", FOUNDER, "«NURLI KELAJAK ISHONCH SERVIS» kompaniyalar guruhi"),
]

# (full name, board role, workplace)
BOARD_MEMBERS = [
    ("O‘roqov Haydar Muhammadiyevich", "chairman", "«NAVOBOD NASLLI PARRANDA» kompaniyalar guruhi, ta’sischi"),
    ("Marupov Baxtiyor Mahmudovich", "deputy", "«SIYOB» kompaniyalar guruhi, ta’sischi"),
    ("Abdullayev Kamol Tal’atovich", "deputy", "«SAG» kompaniyalar guruhi, ta’sischi"),
    ("Komilov Nasim Qobiljonovich", "deputy", "«MEROS» kompaniyalar guruhi, ta’sischi"),
    (
        "Ibragimov Nozir Aliyevich",
        "deputy",
        "Samarqand xalqaro texnologiya universiteti Dual ta’lim markazi direktori, iqtisod fanlari doktori, professor",
    ),
]

# (company, initiator) — Siyob canal project
SIYOB_INITIATORS = [
    ("«SIYOB» kompaniyalar guruhi", "Marupov Baxtiyor Mahmudovich"),
    ("«AGROMIR» kompaniyalar guruhi", "Jalolov Shavkat Amonovich"),
    ("«SHARQ SANOAT» konserni", "Sharipov Shavkat O‘ktamovich"),
    ("«SAG» kompaniyalar guruhi", "Abdullayev Kamol Tal’atovich"),
    ("«NURLI KELAJAK STORY INVEST» MChJ", "Qayumov Akbar Qosimaliyevich"),
    ("«SXF» kompaniyalar guruhi", "To‘rayev Zafar Suyunovich"),
    ("«ME’MOR» MChJ", "Toshev Muzrob"),
    ("«ASIA METALL PROF» QK MChJ", "Baxronov Damir Ravshanovich"),
]

# (year, full name, company, award, description)
RECOGNITIONS = [
    (
        2022,
        "Karimov Ravshan Murodovich",
        "«Metin Group Impeks» MChJ, Bulung‘ur tumani",
        "«Shuhrat» medali",
        "O‘zbekiston Respublikasi Prezidentining 2022-yil 20-avgustdagi qarori bilan respublikaning iqtisodiy qudrati va "
        "eksport salohiyatini oshirishga qo‘shgan katta hissasi uchun.",
    ),
    (
        2023,
        "Shukurullayev Dilshod Dalerovich",
        "«Zarmed Pratiksha Hospital Group» MChJ ta’sischisi, Samarqand shahri",
        "«Do‘stlik» ordeni",
        "O‘zbekiston Respublikasi Prezidentining 2023-yil 18-avgustdagi farmoni bilan.",
    ),
    (
        2023,
        "Norboyev Anvar Ochilovich",
        "«Kattaqo‘rg‘on elektrotexnika zavodi» MChJ direktori, Kattaqo‘rg‘on tumani",
        "«Shuhrat» medali",
        "O‘zbekiston Respublikasi Prezidentining 2023-yil 18-avgustdagi farmoni bilan.",
    ),
    (
        2024,
        "Rustamov Ilhom Aslamovich",
        "«Ahmadbek Qurilish Trio» MChJ bosh direktori, Samarqand shahri",
        "«Do‘stlik» ordeni",
        "O‘zbekiston Respublikasi Prezidentining 2024-yil 14-avgustdagi farmoni bilan.",
    ),
    (
        2024,
        "Ibodullayev Umarjon G‘aybullayevich",
        "«Bekmez Carpet» MChJ direktori, Urgut tumani",
        "«Shuhrat» medali",
        "O‘zbekiston Respublikasi Prezidentining 2024-yil 14-avgustdagi farmoni bilan.",
    ),
    (
        2024,
        "Eshonqulov Shokir Hamdamovich",
        "«Silver Green Tea» oilaviy korxonasi direktori, Payariq tumani",
        "«Shuhrat» medali",
        "O‘zbekiston Respublikasi Prezidentining 2024-yil 14-avgustdagi farmoni bilan.",
    ),
    (
        2025,
        "Abdullayev Kamol Tal’atovich",
        "«Sam Antep Gilam» MChJ ta’sischisi, Samarqand shahri",
        "«O‘zbekiston Respublikasida xizmat ko‘rsatgan tadbirkor» faxriy unvoni",
        "O‘zbekiston Respublikasi Prezidentining 2025-yil 21-avgustdagi farmoni bilan.",
    ),
    (
        2025,
        "Saidmurodov O‘ktam Saidmurodovich",
        "«Stekloplastik» MChJ ta’sischisi va direktorlar kengashi raisi",
        "«O‘zbekiston Respublikasida xizmat ko‘rsatgan tadbirkor» faxriy unvoni",
        "O‘zbekiston Respublikasi Prezidentining 2025-yil 21-avgustdagi farmoni bilan.",
    ),
    (
        2025,
        "To‘rayev Zafar Suyunovich",
        "«SXF Big Stroy Building» MChJ ta’sischisi, Urgut tumani",
        "«Do‘stlik» ordeni",
        "O‘zbekiston Respublikasi Prezidentining 2025-yil 21-avgustdagi farmoni bilan.",
    ),
    (
        2025,
        "Ergashev Shuhrat Sharipovich",
        "«Samarkand Garden Plast» MChJ direktorlar kengashi raisi, Bulung‘ur tumani",
        "«Do‘stlik» ordeni",
        "O‘zbekiston Respublikasi Prezidentining 2025-yil 21-avgustdagi farmoni bilan.",
    ),
    (
        2025,
        "Komilov Nasimjon Qobiljonovich",
        "«STD Health Med» MChJ ta’sischisi, Samarqand shahri",
        "«Shuhrat» medali",
        "O‘zbekiston Respublikasi Prezidentining 2025-yil 21-avgustdagi farmoni bilan.",
    ),
    (
        2025,
        "Sharipov Shavkat O‘ktamovich",
        "«Sharq Sanoat» konserni ta’sischisi",
        "«Turon» xalqaro akademiyasining faxriy a’zoligiga taqdim etilgan",
        "Kengash a’zolarining 2025-yil 13-martdagi yig‘ilishida mamlakatda tadbirkorlikni rivojlantirish va minglab "
        "ish o‘rinlari yaratishdagi ko‘p yillik faoliyati uchun.",
    ),
    (
        2025,
        "Abdullayev Kamol Tal’atovich",
        "«SAG» kompaniyalar guruhi hammuassisi",
        "«Turon» xalqaro akademiyasining faxriy a’zoligiga taqdim etilgan",
        "Kengash a’zolarining 2025-yil 13-martdagi yig‘ilishida mamlakatda tadbirkorlikni rivojlantirish va minglab "
        "ish o‘rinlari yaratishdagi ko‘p yillik faoliyati uchun.",
    ),
]

TEACHERS_DAY_HONOREES = [
    "Niyozova Mar’yam Qodirovna",
    "Qo‘chqorova Gulbeka Allamuratovna",
    "Rahimov Po‘lat Rahimovich",
    "Ziyoyev Fayzullo Ziyoyevich",
    "Saidmurodov O‘ktam Saidmurodovich",
    "O‘roqov Haydar Muhammadiyevich",
    "Sharipov Shavkat O‘ktamovich",
    "Ibragimov Nozir Aliyevich",
    "Yusupov Nosir Fatixovich",
    "Bagirov Nosir Musoyevich",
]
