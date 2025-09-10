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
TYPES = {
    'punt': 1,
    'mededeling': 2,
}
REGEXES = {
    'context': r'(?P<context>(VR)|(VE))',
    'year': r'(?P<year>\d{4})',
    'sessionNr': r'(?P<sessionNr>\d{1,2})',
    'type': r'(?P<type>(punt)|(mededeling))',
    'typeNr': r'(?P<typeNr>\d{1,4})',
    'versionSuffix': rf'(?P<versionSuffix>({")|(".join(map(str.upper, NUMBERS_BY_LATIN_ADVERBIALS.keys()))}))'.replace('()|', ''),
}

DEC_NAME_REGEX = re.compile(rf'^{REGEXES["context"]} PV {REGEXES["year"]}/{REGEXES["sessionNr"]}( - {REGEXES["type"]} {REGEXES["typeNr"]})?{REGEXES["versionSuffix"]}?$')


def compare_decision_piece_names(name1, name2) -> int:
    def unix_time(s): return int(datetime.datetime.strptime(s, "%Y").timestamp())
    #def version(s): return NUMBERS_BY_LATIN_ADVERBIALS[s.lower()] if s else 1
    def type(s): return TYPES[s.lower()] if s else 0 # no type means minutes
    def typeNr(s): return int(s) if s else 0 # no type means minutes

    m1 = DEC_NAME_REGEX.match(name1)
    m2 = DEC_NAME_REGEX.match(name2)
    if m1 and m2:
        return ((unix_time(m1.group("year")) - unix_time(m2.group("year"))) or  # Year descending (oldest first)
                (int(m1.group("sessionNr")) - int(m2.group("sessionNr"))) or  # SessionNr ascending
                (type(m1.group("type")) - type(m2.group("type"))) or  # type, no type < "punt" < "mededeling"
                (typeNr(m1.group("typeNr")) - typeNr(m2.group("typeNr"))))  # typeNr ascending
                #(version(m2.group("versionSuffix")) - version(m1.group("versionSuffix")))) # TODO remove on review, versionNumber does not make any sense here
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
