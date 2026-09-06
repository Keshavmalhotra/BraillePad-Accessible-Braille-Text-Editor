"""Language profiles and the one Liblouis translation boundary."""
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

@dataclass(frozen=True)
class Meaning:
    text: str
    label: str

@dataclass(frozen=True)
class LanguageProfile:
    key: str
    language: str
    script: str
    standard: str
    table: str
    back_table: str | None = None
    rtl: bool = False
    status: str = "bundled Liblouis 3.38.0; Bharati 2.1 conformance requires external validation"
    @property
    def version(self):
        return self.standard

PROFILES = {
 "en": LanguageProfile("en","English","Latin","UEB","en-ueb-g1.ctb","en-ueb-g1.ctb",status="bundled Liblouis 3.38.0"),
 "hi": LanguageProfile("hi","Hindi","Devanagari","Bharati 2.1 target","hi-in-g1.utb"),
 "sa": LanguageProfile("sa","Sanskrit","Devanagari","Bharati 2.1 target","sa-in-g1.utb"),
 "mr": LanguageProfile("mr","Marathi","Devanagari","Bharati 2.1 target","mr-in-g1.utb"),
 "ne": LanguageProfile("ne","Nepali","Devanagari","Bharati 2.1 target","ne.tbl"),
 "as": LanguageProfile("as","Assamese","Bengali-Assamese","Bharati 2.1 target","as-in-g1.utb"),
 "bn": LanguageProfile("bn","Bengali","Bengali-Assamese","Bharati 2.1 target","bn.tbl"),
 "gu": LanguageProfile("gu","Gujarati","Gujarati","Bharati 2.1 target","gu-in-g1.utb"),
 "pa": LanguageProfile("pa","Punjabi","Gurmukhi","Bharati 2.1 target","pa.tbl"),
 "kn": LanguageProfile("kn","Kannada","Kannada","Bharati 2.1 target","kn.tbl"),
 "ml": LanguageProfile("ml","Malayalam","Malayalam","Bharati 2.1 target","ml-in-g1.utb"),
 "or": LanguageProfile("or","Odia","Odia","Bharati 2.1 target","or-in-g1.utb"),
 "ta": LanguageProfile("ta","Tamil","Tamil","Bharati 2.1 target","ta.tbl"),
 "te": LanguageProfile("te","Telugu","Telugu","Bharati 2.1 target","te-in-g1.utb"),
 "ur": LanguageProfile("ur","Urdu","Urdu/Arabic","Urdu Braille","ur-pk-g1.utb","ur-pk-g1.utb",True),
}
TABLES = PROFILES
BrailleTableInfo = LanguageProfile

def canonical_cell(dots: str) -> str:
    if not isinstance(dots, str) or not re.fullmatch(r"[1-6]*", dots):
        raise ValueError(f"invalid Braille cell: {dots!r}")
    return "".join(sorted(set(dots), key=int))

def canonical_sequence(patterns):
    return tuple(canonical_cell(p) for p in patterns)

class LiblouisTable:
    number_sign = "3456"
    def __init__(self, profile):
        self.info = profile; root = Path(__file__).resolve().parents[1] / "vendor"
        self.exe = root / "bin" / "lou_translate.exe"; self.table = root / "share/liblouis/tables" / profile.table
        self.display = root / "share/liblouis/tables/unicode.dis"
    @property
    def standards_backend(self): return f"Liblouis 3.38.0; table={self.info.table}; standard={self.info.standard}"
    @staticmethod
    def _braille(pattern): return chr(0x2800 + sum(1 << (int(dot)-1) for dot in canonical_cell(pattern)))
    def translate_sequence(self, patterns, numeric=False):
        cells = canonical_sequence(patterns)
        if not cells: return ""
        if not self.exe.exists() or not self.table.exists(): raise FileNotFoundError(f"missing Liblouis table: {self.table.name}")
        text = "".join(self._braille(cell) for cell in cells)
        result = subprocess.run([str(self.exe), "-b", "-d", str(self.display), str(self.table)], input=text, text=True, encoding="utf-8", capture_output=True, cwd=str(self.exe.parent.parent), check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return result.stdout.rstrip("\r\n")
    def translate(self, pattern, numeric=False):
        try: value = self.translate_sequence((pattern,), numeric)
        except (OSError, subprocess.SubprocessError, ValueError): value = ""
        return Meaning(value or "?", "braille" if value else "untranslated cell")

class EnglishGrade1(LiblouisTable):
    letters = {"1":"a","12":"b","14":"c","145":"d","15":"e","124":"f","1245":"g","125":"h","24":"i","245":"j","13":"k","123":"l","134":"m","1345":"n","135":"o","1234":"p","12345":"q","1235":"r","234":"s","2345":"t","136":"u","1236":"v","2456":"w","1346":"x","13456":"y","1356":"z"}
    def __init__(self): super().__init__(PROFILES["en"])
    def translate(self, pattern, numeric=False):
        pattern = canonical_cell(pattern)
        if numeric and pattern in self.letters and self.letters[pattern] in "abcdefghij":
            letter = self.letters[pattern]; return Meaning("0" if letter == "j" else str("abcdefghij".index(letter)+1), "number")
        value = super().translate(pattern, numeric)
        if value.label != "untranslated cell": return value
        if pattern == "3456": return Meaning("number sign", "number sign")
        if pattern == "6": return Meaning("capital sign", "capital sign")
        if pattern in self.letters: return Meaning(self.letters[pattern], "letter")
        return value

def available_tables(): return {key: (EnglishGrade1() if key == "en" else LiblouisTable(profile)) for key, profile in PROFILES.items()}
