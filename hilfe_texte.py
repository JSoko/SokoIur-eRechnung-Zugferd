"""
hilfe_texte.py
--------------
Stellt die Handbuch-Datei SokoIur_Hilfe.html direkt bereit.
"""
import os
from config import get_resource_path, get_program_dir


def get_hilfe_html_path() -> str:
    """Sucht SokoIur_Hilfe.html bevorzugt im Programmordner/html, sonst in den Ressourcen."""
    prog_path = os.path.join(get_program_dir(), "html", "SokoIur_Hilfe.html")
    if os.path.isfile(prog_path):
        return prog_path
    return get_resource_path(os.path.join("html", "SokoIur_Hilfe.html"))


def get_doku_html(version_string: str = "") -> str:
    pfad = get_hilfe_html_path()
    with open(pfad, "r", encoding="utf-8") as f:
        return f.read()


def get_changelog_html(version_string: str = "") -> str:
    pfad = get_resource_path(os.path.join("html", "changelog.html"))
    if pfad and os.path.isfile(pfad):
        with open(pfad, "r", encoding="utf-8") as f:
            return f.read()
    return "<p>Kein Changelog vorhanden.</p>"