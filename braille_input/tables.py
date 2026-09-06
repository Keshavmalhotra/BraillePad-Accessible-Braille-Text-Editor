"""Script-independent adapters over the shipped Liblouis translation tables."""
from dataclasses import dataclass
from pathlib import Path
import subprocess

@dataclass(frozen=True)
class Meaning:
    text: str
    label: str

@dataclass(frozen=True)
class BrailleTableInfo:
    key: str; language: str; script: str; standard: str; version: str; filename: str; rtl: bool = False

TABLES = {
 "en": BrailleTableInfo("en","English","Latin","Unified English Braille","UEB","en-ueb-g1.ctb"),
 "hi": BrailleTableInfo("hi","Hindi","Devanagari","Standard Bharati Braille","2.1 (NIEPVD, 2026)","hi-in-g1.utb"),
 "sa": BrailleTableInfo("sa","Sanskrit","Devanagari","Standard Bharati Braille","2.1 (NIEPVD, 2026)","hi-in-g1.utb"),
 "mr": BrailleTableInfo("mr","Marathi","Devanagari","Standard Bharati Braille","2.1 (NIEPVD, 2026)","mr-in-g1.utb"),
 "ne": BrailleTableInfo("ne","Nepali","Devanagari","Standard Bharati Braille","2.1 (NIEPVD, 2026)","ne.tbl"),
 "as": BrailleTableInfo("as","Assamese","Bengali-Assamese","Standard Bharati Braille","2.1 (NIEPVD, 2026)","as-in-g1.utb"),
 "bn": BrailleTableInfo("bn","Bengali","Bengali","Standard Bharati Braille","2.1 (NIEPVD, 2026)","bn.tbl"),
 "gu": BrailleTableInfo("gu","Gujarati","Gujarati","Standard Bharati Braille","2.1 (NIEPVD, 2026)","gu-in-g1.utb"),
 "pa": BrailleTableInfo("pa","Punjabi","Gurmukhi","Standard Bharati Braille","2.1 (NIEPVD, 2026)","pa.tbl"),
 "kn": BrailleTableInfo("kn","Kannada","Kannada","Standard Bharati Braille","2.1 (NIEPVD, 2026)","kn.tbl"),
 "ml": BrailleTableInfo("ml","Malayalam","Malayalam","Standard Bharati Braille","2.1 (NIEPVD, 2026)","ml-in-g1.utb"),
 "or": BrailleTableInfo("or","Odia","Odia","Standard Bharati Braille","2.1 (NIEPVD, 2026)","or-in-g1.utb"),
 "ta": BrailleTableInfo("ta","Tamil","Tamil","Standard Bharati Braille","2.1 (NIEPVD, 2026)","ta.tbl"),
 "te": BrailleTableInfo("te","Telugu","Telugu","Standard Bharati Braille","2.1 (NIEPVD, 2026)","te-in-g1.utb"),
 "ur": BrailleTableInfo("ur","Urdu","Urdu/Arabic","NIEPVD Urdu Braille","official chart; Liblouis ur-pk-g1","ur-pk-g1.utb",True),
}

class LiblouisTable:
    number_sign = "3456"
    def __init__(self, info):
        self.info = info; root = Path(__file__).resolve().parents[1] / "vendor"
        self.exe = root / "bin" / "lou_translate.exe"; self.table = root / "share/liblouis/tables" / info.filename
        self.display = root / "share/liblouis/tables/unicode.dis"
    @property
    def standards_backend(self): return f"Liblouis {self.info.filename} (target: {self.info.standard} {self.info.version})"
    @staticmethod
    def _braille(pattern): return chr(0x2800 + sum(1 << (int(dot)-1) for dot in pattern))
    def translate_sequence(self, patterns, numeric=False):
        text = "".join(self._braille("".join(sorted(set(p)))) for p in patterns)
        if not text or not self.exe.exists() or not self.table.exists(): return ""
        try:
            return subprocess.run([str(self.exe), "-b", "-d", str(self.display), str(self.table)], input=text, text=True, encoding="utf-8", capture_output=True, cwd=str(self.exe.parent.parent), check=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.rstrip("\r\n")
        except (OSError, subprocess.SubprocessError): return ""
    def translate(self, pattern, numeric=False):
        value = self.translate_sequence([pattern], numeric); return Meaning(value or "?", "braille" if value else "untranslated cell")

class EnglishGrade1(LiblouisTable):
    letters = {"1":"a","12":"b","14":"c","145":"d","15":"e","124":"f","1245":"g","125":"h","24":"i","245":"j","13":"k","123":"l","134":"m","1345":"n","135":"o","1234":"p","12345":"q","1235":"r","234":"s","2345":"t","136":"u","1236":"v","2456":"w","1346":"x","13456":"y","1356":"z"}
    def __init__(self): super().__init__(TABLES["en"])
    def translate(self, pattern, numeric=False):
        if numeric and pattern in self.letters and self.letters[pattern] in "abcdefghij": return Meaning("0" if self.letters[pattern] == "j" else str("abcdefghij".index(self.letters[pattern])+1), "number")
        value = super().translate(pattern, numeric)
        if value.label != "untranslated cell": return value
        if pattern == "3456": return Meaning("number sign", "number sign")
        if pattern == "6": return Meaning("capital sign", "capital sign")
        if pattern in self.letters: return Meaning(self.letters[pattern], "letter")
        return value

def available_tables(): return {k: (EnglishGrade1() if k == "en" else LiblouisTable(v)) for k, v in TABLES.items()}
