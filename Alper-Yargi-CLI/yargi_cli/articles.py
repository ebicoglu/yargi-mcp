"""Extract statute-article citations from Turkish court decision text."""
import re
from collections import OrderedDict

# Law number -> short name
NUMBERS = {
    "6098": "TBK", "818": "BK", "6100": "HMK", "1086": "HUMK", "4721": "TMK",
    "743": "MK", "6102": "TTK", "2004": "İİK", "5237": "TCK", "5271": "CMK",
    "2797": "Yargıtay K.", "6502": "TKHK", "7036": "İş Mah. K.", "4857": "İş K.",
    "6325": "Arabuluculuk K.", "3095": "Yasal Faiz K.", "492": "Harçlar K.",
}
# Law name (lowercase prefix) -> short name
NAMES = [
    ("türk borçlar", "TBK"), ("borçlar kanunu", "BK"), ("hukuk muhakemeleri", "HMK"),
    ("hukuk usulü muhakemeleri", "HUMK"), ("türk medeni", "TMK"), ("medeni kanun", "TMK"),
    ("türk ticaret", "TTK"), ("icra ve iflas", "İİK"), ("tüketicinin korunması", "TKHK"),
    ("yasal faiz", "Yasal Faiz K."), ("yargıtay kanunu", "Yargıtay K."),
]
ABBR = ["TBK", "BK", "HMK", "HUMK", "TMK", "MK", "TTK", "İİK", "TCK", "CMK", "TKHK", "İYUK"]
ABBR_RE = "|".join(sorted(ABBR, key=len, reverse=True))

ART = r"(\d{1,4})(?:/\d+)?"
SUFFIX = r"['’`´]?\w{0,5}"

PATTERNS = [
    # TBK'nın 122. maddesi | TBK m. 122 | B.K.105 | TBK 122
    (re.compile(rf"(?<![\w.])({ABBR_RE}|B\.K\.|T\.B\.K\.){SUFFIX}\s*(?:\(\w+\)\s*)?(?:m\.?|madde\w*)?\s*{ART}(?!\d)"), "abbr"),
    # 6098 sayılı Türk Borçlar Kanunu'nun (TBK) 122. maddesi
    (re.compile(rf"(\d{{3,4}})\s+sayılı\s+[^.;\n]{{3,80}}?\W{{1,4}}\w{{0,5}}\s*(?:\(\w+[^)]*\)\s*)?{ART}\s*\.?\s*(?:inci|ıncı|nci|uncu)?\s*madde"), "number"),
    # Türk Borçlar Kanunu'nun 122. maddesi (no law number)
    (re.compile(rf"((?:Türk\s+Borçlar|Borçlar|Hukuk\s+Muhakemeleri|Türk\s+Medeni|Medeni|Türk\s+Ticaret|İcra\s+ve\s+İflas|Yasal\s+Faiz)\s+Kanunu?){SUFFIX}\s*(?:\(\w+\)\s*)?{ART}\s*\.?\s*(?:inci|ıncı|nci|uncu)?\s*madde", re.I), "name"),
]


def _law(kind, raw):
    if kind == "number":
        return NUMBERS.get(raw, f"{raw} sayılı Kanun")
    if kind == "name":
        low = raw.lower()
        for prefix, short in NAMES:
            if low.startswith(prefix) or prefix in low:
                return short
        return raw
    return {"B.K.": "BK", "T.B.K.": "TBK"}.get(raw, raw)


def extract_articles(text):
    """Return OrderedDict {'TBK m.122': context_snippet} in order of first appearance."""
    text = text.replace("\xa0", " ")
    found = OrderedDict()
    for rx, kind in PATTERNS:
        for m in rx.finditer(text):
            key = f"{_law(kind, m.group(1))} m.{m.group(2)}"
            if key not in found:
                s = max(0, m.start() - 120)
                found[key] = " ".join(text[s : m.end() + 120].split())
    return found
