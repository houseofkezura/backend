CURRENCY_CHOICES = [
    ('USD', 'US Dollar (USD)'),
    ('EUR', 'Euro (EUR)'),
    ('NGN', 'Nigerian Naira (NGN)'),
    # ... add additional currencies as needed, up to 163 or fewer if you prefer a subset
]

CURRENCY_SYMBOLS = {
    # Original entries
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CAD": "$",
    "AUD": "$",
    "NGN": "₦",
    
    # Additional currencies
    "AED": "د.إ",     # UAE Dirham
    "AFN": "؋",       # Afghan Afghani
    "AMD": "֏",
    "ANG": "ƒ",
    "AOA": "Kz",
    "AWG": "ƒ",
    "AZN": "₼",
    "ARS": "$",       # Argentine Peso
    "BBD": "$",       # Barbadian Dollar
    "BDT": "৳",       # Bangladeshi Taka
    "BGN": "лв",      # Bulgarian Lev
    "BHD": ".د.ب",    # Bahraini Dinar
    "BIF": "FBu",
    "BND": "$",       # Brunei Dollar
    "BOB": "Bs.",     # Bolivian Boliviano
    "BRL": "R$",      # Brazilian Real
    "BSD": "$",       # Bahamian Dollar
    "BTN": "Nu.",
    "BWP": "P",       # Botswana Pula
    "BYN": "Br",      # Belarusian Ruble
    "BZD": "BZ$",     # Belize Dollar
    "CDF": "FC",
    "CHF": "Fr.",     # Swiss Franc
    "CLP": "$",       # Chilean Peso
    "CNY": "¥",       # Chinese Yuan
    "COP": "$",       # Colombian Peso
    "CRC": "₡",       # Costa Rican Colón
    "CUP": "₱",
    "CVE": "$",
    "CZK": "Kč",      # Czech Koruna
    "DJF": "Fdj",
    "DKK": "kr",      # Danish Krone
    "DOP": "RD$",     # Dominican Peso
    "DZD": "د.ج",     # Algerian Dinar
    "EGP": "£",       # Egyptian Pound
    "FJD": "$",       # Fijian Dollar
    "GHS": "₵",     # Ghanaian Cedi
    "GIP": "£",
    "GMD": "D",
    "GNF": "FG",
    "GYD": "$",
    "GTQ": "Q",       # Guatemalan Quetzal
    "HKD": "HK$",     # Hong Kong Dollar
    "HNL": "L",       # Honduran Lempira
    "HRK": "kn",      # Croatian Kuna
    "HUF": "Ft",      # Hungarian Forint
    "IDR": "Rp",      # Indonesian Rupiah
    "ILS": "₪",       # Israeli Shekel
    "INR": "₹",       # Indian Rupee
    "IQD": "ع.د",
    "IRR": "﷼",
    "JEP": "£",
    "ISK": "kr",      # Icelandic Króna
    "JMD": "J$",      # Jamaican Dollar
    "JOD": "د.ا",     # Jordanian Dinar
    "KES": "KSh",     # Kenyan Shilling
    "KGS": "с",       # Kyrgyzstani Som
    "KHR": "៛",       # Cambodian Riel
    "KMF": "CF",      # Comorian Franc
    "KRW": "₩",       # South Korean Won
    "KWD": "د.ك",     # Kuwaiti Dinar
    "KYD": "$",
    "KZT": "₸",       # Kazakhstani Tenge
    "LAK": "₭",       # Lao Kip
    "LBP": "ل.ل",     # Lebanese Pound
    "LKR": "Rs",      # Sri Lankan Rupee
    "LRD": "$",       # Liberian Dollar
    "LSL": "L",       # Lesotho Loti
    "LYD": "ل.د",
    "MAD": "د.م.",    # Moroccan Dirham
    "MDL": "L",       # Moldovan Leu
    "MGA": "Ar",
    "MKD": "ден",     # Macedonian Denar
    "MMK": "K",       # Myanmar Kyat
    "MOP": "MOP$",    # Macanese Pataca
    "MUR": "₨",       # Mauritian Rupee
    "MVR": "Rf",      # Maldivian Rufiyaa
    "MWK": "MK",      # Malawian Kwacha
    "MXN": "$",       # Mexican Peso
    "MYR": "RM",      # Malaysian Ringgit
    "MZN": "MT",      # Mozambican Metical
    "NAD": "$",       # Namibian Dollar
    "NIO": "C$",
    "NOK": "kr",      # Norwegian Krone
    "NPR": "₨",       # Nepalese Rupee
    "NZD": "$",       # New Zealand Dollar
    "OMR": "ر.ع.",    # Omani Rial
    "PAB": "B/.",     # Panamanian Balboa
    "PEN": "S/.",     # Peruvian Sol
    "PGK": "K",       # Papua New Guinean Kina
    "PHP": "₱",       # Philippine Peso
    "PKR": "₨",       # Pakistani Rupee
    "PLN": "zł",      # Polish Złoty
    "PYG": "₲",       # Paraguayan Guaraní
    "QAR": "﷼",       # Qatari Riyal
    "RON": "lei",     # Romanian Leu
    "RSD": "дин.",    # Serbian Dinar
    "RUB": "₽",       # Russian Ruble
    "RWF": "FRw",     # Rwandan Franc
    "SAR": "﷼",       # Saudi Riyal
    "SBD": "$",       # Solomon Islands Dollar
    "SCR": "₨",       # Seychellois Rupee
    "SDG": "ج.س.",    # Sudanese Pound
    "SEK": "kr",      # Swedish Krona
    "SGD": "S$",      # Singapore Dollar
    "SLL": "Le",      # Sierra Leonean Leone
    "SOS": "Sh",      # Somali Shilling
    "SRD": "$",       # Surinamese Dollar
    "STN": "Db",      # São Tomé and Príncipe Dobra
    "SYP": "£",       # Syrian Pound
    "SZL": "L",       # Swazi Lilangeni
    "THB": "฿",       # Thai Baht
    "TJS": "ЅМ",      # Tajikistani Somoni
    "TMT": "m",       # Turkmenistani Manat
    "TND": "د.ت",     # Tunisian Dinar
    "TOP": "T$",      # Tongan Paʻanga
    "TRY": "₺",       # Turkish Lira
    "TTD": "TT$",     # Trinidad and Tobago Dollar
    "TWD": "NT$",     # New Taiwan Dollar
    "TZS": "Sh",      # Tanzanian Shilling
    "UAH": "₴",       # Ukrainian Hryvnia
    "UGX": "USh",     # Ugandan Shilling
    "UYU": "$U",      # Uruguayan Peso
    "UZS": "so'm",    # Uzbekistani Som
    "VES": "Bs.S",    # Venezuelan Bolívar
    "VND": "₫",       # Vietnamese Đồng
    "VUV": "Vt",      # Vanuatu Vatu
    "WST": "T",       # Samoan Tālā
    "XAF": "FCFA",    # CFA Franc BEAC
    "XCD": "$",       # East Caribbean Dollar
    "XOF": "CFA",     # CFA Franc BCEAO
    "XPF": "₣",       # CFP Franc
    "YER": "﷼",       # Yemeni Rial
    "ZAR": "R",       # South African Rand
    "ZMW": "ZK",      # Zambian Kwacha
    "ZWL": "$",       # Zimbabwe Dollar
}