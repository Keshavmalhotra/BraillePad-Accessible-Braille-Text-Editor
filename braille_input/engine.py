from dataclasses import dataclass, asdict
from .tables import EnglishGrade1, available_tables, canonical_cell, TABLES

@dataclass(frozen=True)
class BrailleCell:
    dots: str
    meaning: str
    label: str
    mode: str = "literary"

class CellComposer:
    def __init__(self): self._dots = set()
    @property
    def dots(self): return "".join(str(d) for d in sorted(self._dots))
    def add(self, key):
        if key not in "123456": return False
        self._dots.add(int(key)); return True
    def remove_last(self):
        if self._dots: self._dots.remove(max(self._dots))
    def clear(self): self._dots.clear()

class BrailleDocument:
    def __init__(self, table=None):
        self.table = table or EnglishGrade1(); self.cells = []; self.cursor = 0; self.numeric = False; self.capital_pending = False
    @property
    def language_key(self): return self.table.info.key
    def set_table(self, key):
        self.table = available_tables()[key]
    @property
    def text(self):
        return self.render_text()
    def render_text(self):
        """Render cells by word sequence; a cell is not a word boundary."""
        out=[]; i=0
        while i < len(self.cells):
            if not self.cells[i].dots:
                out.append(self.cells[i].meaning); i += 1; continue
            j=i
            while j < len(self.cells) and self.cells[j].dots: j += 1
            patterns=[c.dots for c in self.cells[i:j]]
            translated=self.table.translate_sequence(patterns, self.numeric) if hasattr(self.table, "translate_sequence") else ""
            if translated and self.language_key != "en": out.append(translated)
            else: out.extend(c.meaning if c.label not in ("number sign", "capital sign") and c.dots != "6" else "" for c in self.cells[i:j])
            i=j
        return "".join(out)
    def word_patterns_at(self, index):
        start=index
        while start > 0 and self.cells[start-1].dots: start -= 1
        end=index
        while end < len(self.cells) and self.cells[end].dots: end += 1
        return start, [c.dots for c in self.cells[start:end]]
    def commit(self, dots):
        pattern = canonical_cell(dots)
        meaning = self.table.translate(pattern, self.numeric)
        # Indicators are part of the input stream, but are not printable text.
        if pattern == "6":
            self.capital_pending = True
        elif self.capital_pending and meaning.text and meaning.text.isalpha():
            meaning = type(meaning)(meaning.text.upper(), meaning.label)
            self.capital_pending = False
        cell = BrailleCell(pattern, meaning.text, meaning.label, "numeric" if self.numeric else "literary")
        self.cells.insert(self.cursor, cell); self.cursor += 1
        if pattern == self.table.number_sign: self.numeric = True
        elif self.numeric and meaning.label == "number" and meaning.text == "0": self.numeric = False
        return cell
    def space(self):
        self.cells.insert(self.cursor, BrailleCell("", " ", "space")); self.cursor += 1; self.numeric = False
    def line_break(self):
        self.cells.insert(self.cursor, BrailleCell("", "\n", "linebreak")); self.cursor += 1; self.numeric = False
    def backspace(self):
        if self.cursor: self.cursor -= 1; return self.cells.pop(self.cursor)
    def snapshot(self): return {"version":2,"language":self.language_key,"cursor":self.cursor,"numeric":self.numeric,"capital_pending":self.capital_pending,"cells":[asdict(c) for c in self.cells]}
    @classmethod
    def from_snapshot(cls, data):
        doc=cls(available_tables().get(data.get("language"), EnglishGrade1())); doc.cells=[BrailleCell(**c) for c in data["cells"]]; doc.cursor=data.get("cursor",len(doc.cells)); doc.numeric=data.get("numeric",False); doc.capital_pending=data.get("capital_pending",False); return doc
