"""Industrialists' Forum results (translated from the official records)."""

D1, D2, D3, WIN, SPECIAL = "1", "2", "3", "winner", "special"


def podium(first, second, third):
    return [(D1, first, ""), (D2, second, ""), (D3, third, "")]


FORUM_INTRO = (
    "<p>Yangi O‘zbekiston iqtisodiy siyosatida sanoat o‘sishi, import o‘rnini bosish va mahalliy ishlab chiqaruvchilar "
    "o‘rtasida sanoat kooperatsiyasini rivojlantirish alohida o‘rin tutadi.</p>"
    "<p>Ilg‘or ishlab chiqarish korxonalarini rag‘batlantirish, ularning texnologik va boshqaruv tajribasini tarqatish "
    "maqsadida «Samarqand viloyati sanoatchilar forumi» tashkil etildi. Forum doirasida turli nominatsiyalar bo‘yicha "
    "mukofotlash bilan birga ishlab chiqarishni lokalizatsiya qilish, sanoat kooperatsiyasi va tarmoqlar kesimida "
    "eksportni kengaytirish masalalari muhokama qilinadi.</p>"
)

EDITIONS = [
    {
        "year": 2023,
        "results_year": 2022,
        "title": "Samarqand viloyati sanoatchilar forumi — 2023",
        "dates": "30–31 may 2023",
        "intro": "<p>2022-yil sanoat rivoji yakunlari bo‘yicha nominatsiyalar g‘oliblari.</p>",
        "nominations": [
            (
                "2022-yilda ishlab chiqarishni lokalizatsiya qilish sohasidagi eng namunali korxona",
                podium("«AZIA METALL PROF» QK MChJ", "«MIRANKUL CONSTRUCTION MATERIALS» MChJ", "«KATTAQO‘RG‘ON ELEKTRO TEXNIKA ZAVODI» MChJ"),
            ),
            (
                "2022-yilda sanoat kooperatsiyasi sohasidagi eng namunali korxona",
                podium("«STEKLOPLASTIK» MChJ", "«MITAN YOG‘DU ELEKTRIK» MChJ", "«SAM NEGIN» MChJ"),
            ),
            (
                "2022-yilda sanoat sohasidagi eng yirik investitsiya loyihasi",
                podium("«BAHT SAMARKAND TEKS» MChJ", "«AZIA METALL PROF» QK MChJ", "«SMART HYGIENE FACILITIES» MChJ"),
            ),
            (
                "2022-yilning eng namunali brendi",
                [
                    (D1, "«SAG» savdo belgisi", "«Sam Antep Gilam» MChJ"),
                    (D2, "«Pure Milky» savdo belgisi", "«SIYOB Group» kompaniyalar guruhi"),
                    (D3, "«Nishon Baxt» savdo belgisi", "«Nishon Baxt» XK"),
                ],
            ),
            (
                "2022-yilning eng namunali eksportyor korxonasi (yirik korxonalar orasida)",
                podium("«AZIA METALL PROF» QK MChJ", "«PAXTACHI KLASTER» MChJ", "«OHALIK OLTIN BOG‘I MEVASI» MChJ"),
            ),
            (
                "2022-yilning eng namunali eksportyor korxonasi (o‘rta va kichik korxonalar orasida)",
                podium("«JOMBOY NASLLI PARRANDA» MChJ", "«DKIZ 2022» MChJ", "«URGUT KAMOL JAMOL» MChJ"),
            ),
            (
                "2023-yilning eng namunali ijtimoiy faol korxonasi",
                podium("«SXF Group» kompaniyalar guruhi", "«Nurli Kelajak Ishonch Servis» MChJ", "«Sam Antep Gilam» MChJ"),
            ),
            (
                "Ommaviy axborot vositalari xodimlari orasidagi nominatsiya",
                [
                    (SPECIAL, "O‘ktam Xudoyberdiyev", "«Zarafshon» gazetasi muxbiri, jurnalist"),
                    (SPECIAL, "Yulduz Haydarova", "«Samarkandskiy vestnik» gazetasi muxbiri, jurnalist"),
                    (SPECIAL, "Jamshed Obidov", "«Ovozi Samarqand» gazetasi muxbiri, jurnalist"),
                    (SPECIAL, "Lutfulla Shomurodov", "«O‘zbekiston — 24» telekanalining Samarqand viloyatidagi muxbiri"),
                    (SPECIAL, "Ikrom Mamadaliyev", "«2022-yilning eng faol teleoperatori» — viloyat teleradiokompaniyasi"),
                ],
            ),
        ],
    },
    {
        "year": 2024,
        "results_year": 2023,
        "title": "Samarqand viloyati sanoatchilar forumi — 2024",
        "dates": "16–17 may 2024",
        "intro": "<p>2023-yil sanoat rivoji yakunlari bo‘yicha nominatsiyalar g‘oliblari.</p>",
        "nominations": [
            (
                "2023-yilda ishlab chiqarishni lokalizatsiya qilish sohasidagi eng namunali korxona",
                podium("«NBA ALLIANZ» MChJ", "«SATURN METAL QAYTA ISHLASH» MChJ", "«SAMARKAND GOLDEN COLORS» MChJ"),
            ),
            (
                "2023-yilda sanoat kooperatsiyasi sohasidagi eng namunali korxona",
                podium("«MITAN YOG‘DU ELEKTRIK» MChJ", "«ESMAK» MChJ", "«SHERDOR ELITA PLAST» MChJ"),
            ),
            (
                "2023-yilda oziq-ovqat sanoatidagi eng namunali korxona",
                podium("«MAROQAND GOLD OIL EXTRACTION» MChJ", "«PAXTACHI RODNIK» MChJ", "«NISHON GROUP» MChJ"),
            ),
            (
                "2023-yilda turizm sohasi uchun mahsulot ishlab chiqaruvchi eng namunali korxona",
                podium("«KUMUSH TOLA» XK", "«ASIA INVEST TEXTILE» MChJ", "«SAIDOV ABDULLO» YaTT"),
            ),
            (
                "2023-yilda turizm sohasidagi eng namunali korxona",
                podium("«SOF EXPO SAMARKAND» ko‘rgazma markazi", "«SILK TUR» MChJ", "«BO‘STON TRAVEL» MChJ"),
            ),
            (
                "2023-yilning eng namunali brendi",
                [
                    (D1, "«KLEO» savdo belgisi", "«SAM FERRE» MChJ"),
                    (D2, "«AGRO BRAVO» savdo belgisi", "«AGRO BRAVO» MChJ"),
                    (D3, "«MONDELUX» savdo belgisi", "«GULOBOD MEBEL» MChJ"),
                ],
            ),
            (
                "2023-yilda sanoat mahsulotlarini eksport qiluvchi eng namunali korxona",
                podium("«BRADJUS» MChJ", "«HASID TEXTILE» YaTT", "«ASIA TAREN» MChJ"),
            ),
            (
                "2023-yilda qishloq xo‘jaligi mahsulotlarini eksport qiluvchi eng namunali korxona",
                podium("«ANSORJON AGRO SAXOVATI» MChJ", "«AGRO SOY PLAST» MChJ", "«HAKAN AGRO INVEST» MChJ"),
            ),
            (
                "2023-yilda elektrotexnika sanoatidagi eng namunali korxona",
                podium("«SAM NUR TAFRIZ» MChJ", "«TESPACK INVESTMENT» MChJ", "«KATTAQO‘RG‘ON ELEKTROTEXNIKA ZAVODI» MChJ"),
            ),
            (
                "2023-yilda farmatsevtika sanoatidagi eng namunali korxona",
                podium("«OPTIMA SOBIRJON» MChJ", "«MAXMADJON NURAFSHON» XK", "«FORTUNA URGUT MEDICAL» MChJ"),
            ),
            (
                "2023-yilda mebel sanoatidagi eng namunali korxona",
                podium("«ERKIN SAVDO MOBIL SERVIS» MChJ", "«MEHR MEBELI» oilaviy korxonasi", "«SABINA–S» MChJ"),
            ),
            (
                "2023-yilda qurilish materiallari sanoatidagi eng namunali korxona",
                podium("«KAFOLAT-STIL» MChJ", "«FOX PIPES INNOVATION» MChJ", "«XITOY BESH BARMOQ QURILISH MATERIALLARI» YaTT"),
            ),
        ],
    },
    {
        "year": 2025,
        "results_year": 2024,
        "title": "Samarqand viloyati sanoatchilar forumi — 2025",
        "dates": "17–18 aprel 2025",
        "intro": "<p>2024-yil sanoat rivoji yakunlari bo‘yicha nominatsiyalar g‘oliblari.</p>",
        "nominations": [
            (
                "2024-yilda sanoat kooperatsiyasi sohasidagi eng namunali korxona",
                [(WIN, "«SAM FERRE» MChJ", "Urgut tumani")],
            ),
            (
                "2024-yilda ishlab chiqarishni lokalizatsiya qilish sohasidagi eng namunali korxona",
                [(WIN, "O‘zbekiston-Xitoy «AZIA METALL PROF» QK MChJ", "Samarqand shahri")],
            ),
            (
                "2024-yilda sanoat mahsulotlari eksporti sohasidagi eng namunali korxona",
                [(WIN, "«NAVOBOD NASLLI PARRANDA» fermer xo‘jaligi", "Samarqand tumani")],
            ),
            (
                "2024-yilning eng namunali brendi",
                [(WIN, "BLISS, MEVA JUICE, MARINELLE savdo belgilari", "«AGROMIR» QK, Samarqand tumani")],
            ),
        ],
    },
]
