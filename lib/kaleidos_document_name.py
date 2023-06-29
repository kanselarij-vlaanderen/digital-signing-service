import datetime
import re

NUMBERS_BY_LATIN_ADVERBIALS = {
    '': 1,
    'bis': 2,
    'ter': 3,
    'quater': 4,
    'quinquies': 5,
    'sexies': 6,
    'septies': 7,
    'octies': 8,
    'novies': 9,
    'decies': 10,
    'undecies': 11,
    'duodecies': 12,
    'ter decies': 13,
    'quater decies': 14,
    'quindecies': 15,
}

REGEXES = {
    'date': r'(?P<date>[12][90][0-9]{2} [0-3][0-9][01][0-9])',
    'casePrefix': r'(?P<casePrefix>( VV)|())',  # VV = Vlaamse Veerkracht
    'docType': r'(?P<docType>(DOC)|(DEC)|(MED))',
    'caseNr': r'(?P<caseNr>\d{4})',
    'index': r'(?P<index>\d{1,3})',
    'versionSuffix': rf'(?P<versionSuffix>({")|(".join(map(str.upper, NUMBERS_BY_LATIN_ADVERBIALS.keys()))}))'.replace('()|', ''),
}

DOC_NAME_REGEX = re.compile(rf'VR {REGEXES["date"]}{REGEXES["casePrefix"]} {REGEXES["docType"]}\.{REGEXES["caseNr"]}([/-]{REGEXES["index"]})?(.*?){REGEXES["versionSuffix"]}?$')


def compare_piece_names(name1, name2) -> int:
    def unix_time(s): return int(datetime.datetime.strptime(s, "%Y %d%m").timestamp())
    def version(s): return NUMBERS_BY_LATIN_ADVERBIALS[s.lower()] if s else 1

    m1 = DOC_NAME_REGEX.match(name1)
    m2 = DOC_NAME_REGEX.match(name2)
    if m1 and m2:
        return ((int(m2.group("caseNr")) - int(m1.group("caseNr"))) or  # Case number descending (newest first)
                (int(m1.group("index")) - int(m2.group("index")) or  # Index ascending
                (unix_time(m2.group("date")) - unix_time(m1.group("date"))) or  # Date descending (newest first)
                (version(m2.group("versionSuffix")) - version(m1.group("versionSuffix")))))  # versionNumber descending (newest first)
    elif m1:
        return -1
    elif m2:
        return 1
    elif name1 == name2:
        return 0
    elif name1 < name2:
        return -1
    else:
        return 1
