"""
hilfe_texte.py
--------------
Stellt Handbuch- und Changelog-HTML aus dem lokalen Programmdatenverzeichnis bereit.
"""
import os
from config import get_appdata_dir, get_resource_path, get_program_dir


def get_local_html_dir() -> str:
    return os.path.join(get_appdata_dir(), "html")


def _resolve_html_file(filename: str) -> str:
    candidates = [
        os.path.join(get_local_html_dir(), filename),
        os.path.join(get_program_dir(), "html", filename),
        get_resource_path(os.path.join("html", filename)),
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return candidates[0]


def get_hilfe_html_path() -> str:
    return _resolve_html_file("SokoIur_Hilfe.html")


def get_doku_html(version_string: str = "") -> str:
    pfad = get_hilfe_html_path()
    with open(pfad, "r", encoding="utf-8") as f:
        return f.read()


def get_changelog_html(version_string: str = "") -> str:
    pfad = _resolve_html_file("changelog.html")
    if pfad and os.path.isfile(pfad):
        with open(pfad, "r", encoding="utf-8") as f:
            return f.read()
    return "<p>Kein Changelog vorhanden.</p>"