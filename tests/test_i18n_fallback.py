from utils.i18n import i18n


def localize(lang: str, key: str, default: str) -> str:
    return i18n.get(lang, {}).get(key) or i18n.get("en", {}).get(key) or default


def test_localize_falls_back_to_default_when_key_is_missing():
    assert localize("en", "missing_key", "fallback") == "fallback"
    assert localize("missing_lang", "missing_key", "fallback") == "fallback"
