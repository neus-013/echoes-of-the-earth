import json
import os

_strings = {}
_current_lang = "ca"


def load_language(lang_code):
    global _strings, _current_lang
    _current_lang = lang_code
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base_dir, "data", "i18n", f"{lang_code}.json")
    with open(path, "r", encoding="utf-8") as f:
        _strings = json.load(f)


def t(key, **kwargs):
    text = _strings.get(key, f"[{key}]")
    if kwargs:
        for k, v in kwargs.items():
            text = text.replace(f"{{{k}}}", str(v))
    return text


def get_language():
    return _current_lang
