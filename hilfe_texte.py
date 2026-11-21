"""
hilfe_texte.py
--------------
Lädt Handbuch und Changelog aus HTML-Dateien und stellt Dokumentationsdateien
im Programmpfad (mit Fallback auf AppData) bereit.
"""
import os
import re
import json
import shutil
from config import get_resource_path, get_program_dir, get_appdata_dir


def _source_signature() -> dict:
    files = ["handbuch.html", "changelog.html"]
    sig = {}
    for name in files:
        p = get_resource_path(os.path.join("html", name))
        try:
            sig[name] = os.path.getmtime(p)
        except OSError:
            sig[name] = 0.0
    return sig


def get_doku_target_dir() -> str:
    """Zielverzeichnis für generierte HTML-/MD-Doku im Programmpfad."""
    return os.path.join(get_program_dir(), "html")


def _sync_doc_assets(target_dir: str) -> None:
    """Kopiert alle Bilddateien (z. B. .png) aus dem HTML-Ressourcenordner in das Zielverzeichnis."""
    src_html_dir = get_resource_path("html")
    if not src_html_dir or not os.path.isdir(src_html_dir):
        return

    allowed_ext = {".png", ".webp", ".jpg", ".jpeg"}
    try:
        for fname in os.listdir(src_html_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in allowed_ext:
                continue
            src_path = os.path.join(src_html_dir, fname)
            dst_path = os.path.join(target_dir, fname)
            if os.path.isfile(src_path):
                try:
                    if os.path.abspath(src_path) != os.path.abspath(dst_path):
                        shutil.copy2(src_path, dst_path)
                except Exception:
                    pass
    except Exception:
        pass


def ensure_doku_files(target_dir: str = None, version_string: str = "1.000", force: bool = False) -> dict:
    """
    Schreibt Hilfe-, Changelog-, Body- und Markdown-Dateien bevorzugt in `target_dir`
    (Programmpfad/html) und weicht bei fehlenden Schreibrechten auf `get_appdata_dir()` aus.
    """
    primary_dir = target_dir or get_doku_target_dir()
    fallback_dir = get_appdata_dir()

    chosen_dir = primary_dir
    try:
        os.makedirs(primary_dir, exist_ok=True)
        test_file = os.path.join(primary_dir, ".write_test")
        with open(test_file, "w", encoding="utf-8") as tf:
            tf.write("ok")
        os.remove(test_file)
    except OSError:
        chosen_dir = fallback_dir
        os.makedirs(chosen_dir, exist_ok=True)

    paths = {
        "hilfe_html": os.path.join(chosen_dir, "SokoIur_Hilfe.html"),
        "snippet_html": os.path.join(chosen_dir, "html.txt"),
        "changelog_html": os.path.join(chosen_dir, "changelog.html"),
        "changelog_snippet": os.path.join(chosen_dir, "clg.txt"),
        "hilfe_md": os.path.join(chosen_dir, "SokoIur_Hilfe.md"),
        "changelog_md": os.path.join(chosen_dir, "changelog.md"),
    }
    meta_path = os.path.join(chosen_dir, "doku_meta.json")
    current_sig = _source_signature()

    needs_update = force or not all(os.path.exists(p) for p in paths.values())
    if not needs_update and os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            if meta.get("version") != str(version_string) or meta.get("sources") != current_sig:
                needs_update = True
        except Exception:
            needs_update = True

    if needs_update:
        doku_html = get_doku_html(version_string)
        changelog_html = get_changelog_html(version_string)

        with open(paths["hilfe_html"], "w", encoding="utf-8") as f:
            f.write(doku_html)
        with open(paths["snippet_html"], "w", encoding="utf-8") as f:
            f.write(_extract_body(doku_html, "<p>Handbuch-Inhalt konnte nicht extrahiert werden.</p>"))

        with open(paths["changelog_html"], "w", encoding="utf-8") as f:
            f.write(changelog_html)
        with open(paths["changelog_snippet"], "w", encoding="utf-8") as f:
            f.write(_extract_body(changelog_html, "<p>Changelog-Inhalt konnte nicht extrahiert werden.</p>"))

        with open(paths["hilfe_md"], "w", encoding="utf-8") as f:
            f.write(html_to_md(doku_html))
        with open(paths["changelog_md"], "w", encoding="utf-8") as f:
            f.write(html_to_md(changelog_html))

        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({"version": str(version_string), "sources": current_sig}, f, indent=2)
        except Exception:
            pass

    _sync_doc_assets(chosen_dir)
    return paths


def _load_template(filename: str, version_string: str) -> str:
    pfad = get_resource_path(os.path.join("html", filename))
    with open(pfad, "r", encoding="utf-8") as f:
        html = f.read()
    return html.replace("__VERSION__", str(version_string))


def get_doku_html(version_string: str) -> str:
    return _load_template("handbuch.html", version_string)


def get_changelog_html(version_string: str) -> str:
    return _load_template("changelog.html", version_string)


def _extract_body(full_html: str, fallback_msg: str) -> str:
    start_marker = "<body>"
    end_marker = '<hr style="border: 0; border-top: 1px solid #ddd; margin: 40px 0 20px 0;">'
    start_pos = full_html.find(start_marker)
    end_pos = full_html.find(end_marker)
    if start_pos != -1 and end_pos != -1:
        return full_html[start_pos + len(start_marker):end_pos].strip()
    return fallback_msg


def get_doku_body_html(version_string: str) -> str:
    return _extract_body(
        get_doku_html(version_string),
        "<p>Handbuch-Inhalt konnte nicht extrahiert werden.</p>",
    )


def get_changelog_body_html(version_string: str) -> str:
    return _extract_body(
        get_changelog_html(version_string),
        "<p>Changelog-Inhalt konnte nicht extrahiert werden.</p>",
    )


def html_to_md(html_text: str) -> str:
    body_match = re.search(r"<body>(.*?)</body>", html_text, re.DOTALL | re.IGNORECASE)
    text = body_match.group(1) if body_match else html_text

    text = re.sub(r'<div class="toc">.*?</div>', "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<h1[^>]*>(.*?)</h1>", r"# \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<h2[^>]*>(.*?)</h2>", r"## \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<h3[^>]*>(.*?)</h3>", r"### \1\n", text, flags=re.IGNORECASE)

    text = re.sub(r"<strong[^>]*>(.*?)</strong>", r"**\1**", text, flags=re.IGNORECASE)
    text = re.sub(r"<b[^>]*>(.*?)</b>", r"**\1**", text, flags=re.IGNORECASE)
    text = re.sub(r"<em[^>]*>(.*?)</em>", r"*\1*", text, flags=re.IGNORECASE)
    text = re.sub(r"<code[^>]*>(.*?)</code>", r"`\1`", text, flags=re.IGNORECASE)
    text = re.sub(r'<a[^>]*href="(.*?)"[^>]*>(.*?)</a>', r"[\2](\1)", text, flags=re.IGNORECASE)
    text = re.sub(r"<li[^>]*>(.*?)</li>", r"* \1\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>(.*?)</p>", r"\1\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<hr[^>]*>", "---\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)

    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&copy;", "©")
        .replace("&rarr;", "->")
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def get_doku_md(version_string: str) -> str:
    return html_to_md(get_doku_html(version_string))


def get_changelog_md(version_string: str) -> str:
    return html_to_md(get_changelog_html(version_string))