import json
from pathlib import Path

class LangResolver:
    def __init__(self, inventory_path="languages.json", aliases_path=None):
        with open(inventory_path, encoding="utf-8") as f:
            self.data = json.load(f)

        self.by_glotlid = {d["glotlid"].lower(): d for d in self.data}
        self.by_iso3 = {d["iso639_3"].lower(): d for d in self.data}
        self.by_iso1 = {d["iso639_1"].lower(): d for d in self.data if d["iso639_1"]}
        self.by_name = {d["name"].lower(): d for d in self.data if d.get("name")}

        self.aliases = {}
        if aliases_path:
            with open(aliases_path, encoding="utf-8") as f:
                self.aliases = json.load(f)

    def resolve(self, inp, prefer_script=None, expand=False):
        if inp is None:
            return None
        s = inp.strip().lower()

        # Aliases (umbrella categories)
        if s in self.aliases:
            return self.aliases[s] if expand else self.aliases[s][0]

        if s in self.by_glotlid:
            return self.by_glotlid[s]["glotlid"]

        if s in self.by_iso1:
            return self._pick_script(self.by_iso1[s], prefer_script)

        if s in self.by_iso3:
            return self._pick_script(self.by_iso3[s], prefer_script)

        if s in self.by_name:
            return self._pick_script(self.by_name[s], prefer_script)

        raise ValueError(f"Unrecognised language: {inp}")

    def _pick_script(self, entry, prefer_script):
        iso3 = entry["iso639_3"].lower()
        matches = [d for d in self.data if d["iso639_3"].lower() == iso3]
        if prefer_script:
            for m in matches:
                if m["script"].lower() == prefer_script.lower():
                    return m["glotlid"]
        return matches[0]["glotlid"]
