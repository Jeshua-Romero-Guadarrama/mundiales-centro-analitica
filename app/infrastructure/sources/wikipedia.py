# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Adaptador de scraping de Wikipedia: clasificaciones y resultados del torneo."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone

from ...core.config import WIKI_URLS
from .. import http

MATCH_SCORE_RE = re.compile(r"(\d+)\s*[–-]\s*(\d+)")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s))
    return "".join(c for c in s if not unicodedata.combining(c)).lower().strip()


def _parse_kickoff(text: str) -> str | None:
    """Extrae la fecha/hora del partido en UTC a partir del texto del recuadro."""
    iso = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if not iso:
        return None
    y, mo, d = int(iso.group(1)), int(iso.group(2)), int(iso.group(3))
    hh, mm = 12, 0
    tm = re.search(r"(\d{1,2}):(\d{2})\s*(a\.m\.|p\.m\.|am|pm)?", text, re.I)
    if tm:
        hh, mm = int(tm.group(1)), int(tm.group(2))
        ap = (tm.group(3) or "").lower().replace(".", "")
        if ap == "pm" and hh != 12:
            hh += 12
        elif ap == "am" and hh == 12:
            hh = 0
    off = 0
    om = re.search(r"UTC\s*([+\-−])\s*(\d{1,2})", text)
    if om:
        off = (-1 if om.group(1) in "-−" else 1) * int(om.group(2))
    try:
        local = datetime(y, mo, d, hh, mm, tzinfo=timezone.utc)
        return (local - timedelta(hours=off)).isoformat()
    except ValueError:
        return None


def _download(url: str) -> str | None:
    try:
        r = http.get(url, timeout=25)
        r.raise_for_status()
        r.encoding = "utf-8"  # Wikipedia siempre es UTF-8
        return r.text
    except Exception as exc:
        print(f"[wiki] descarga fallida {url}: {exc}")
        return None


def _clean_team(name: str) -> str:
    name = re.sub(r"\[.*?\]|\(.*?\)", "", str(name))
    name = re.sub(r"\s*vte\s*$", "", name)  # quita los enlaces "v-t-e" del final
    return name.strip()


def fetch_group_standings() -> dict[str, list[dict]]:
    """Clasificaciones reales de cada grupo (Pos, Pld, W, D, L, GF, GA, Pts).

    Devuelve {"A": [filas], ...} con los 12 grupos en orden. Es la fuente fiable
    para reflejar los partidos ya jugados del torneo.
    """
    import pandas as pd
    from io import StringIO

    for url in WIKI_URLS:
        html = _download(url)
        if not html:
            continue
        try:
            tables = pd.read_html(StringIO(html))
        except Exception as exc:
            print(f"[wiki] read_html fallo: {exc}")
            continue

        grupos: list[list[dict]] = []
        for t in tables:
            cols = {str(c).lower().strip(): c for c in t.columns}
            keys = " ".join(cols.keys())
            if "pld" not in keys or "pts" not in keys or len(t) != 4:
                continue
            teamcol = next((c for k, c in cols.items() if k.startswith("team")), None)
            if teamcol is None:
                continue

            def pick(*names):
                for n in names:
                    if n in cols:
                        return cols[n]
                return None

            cmap = {k: pick(k) for k in ("pld", "w", "d", "l", "gf", "ga", "pts")}
            if any(v is None for v in cmap.values()):
                continue
            filas, ok = [], True
            for _, r in t.iterrows():
                try:
                    filas.append({
                        "name": _clean_team(r[teamcol]),
                        "pld": int(r[cmap["pld"]]), "w": int(r[cmap["w"]]),
                        "d": int(r[cmap["d"]]), "l": int(r[cmap["l"]]),
                        "gf": int(r[cmap["gf"]]), "ga": int(r[cmap["ga"]]),
                        "pts": int(r[cmap["pts"]]),
                    })
                except Exception:
                    ok = False
                    break
            if ok and len(filas) == 4:
                grupos.append(filas)

        if len(grupos) == 12:
            letras = "ABCDEFGHIJKL"
            out = {letras[i]: grupos[i] for i in range(12)}
            jugados = sum(f["pld"] for g in out.values() for f in g) // 2
            print(f"[wiki] clasificaciones de 12 grupos ({jugados} partidos jugados)")
            return out
    return {}


def fetch_matches(known: dict[str, str]) -> list[dict]:
    """Calendario real del torneo: enfrentamientos, fecha y marcador.

    `known` es {nombre_normalizado: nombre_canonico} de las selecciones de la
    base de datos. Solo se devuelven los partidos entre selecciones conocidas
    (fase de grupos), con su resultado si ya se jugaron.
    """
    from bs4 import BeautifulSoup

    for url in WIKI_URLS:
        html = _download(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "lxml")
        boxes = soup.select(".footballbox")
        if not boxes:
            continue

        out: list[dict] = []
        for b in boxes:
            home_el = b.select_one(".fhome")
            score_el = b.select_one(".fscore")
            away_el = b.select_one(".faway")
            if not (home_el and score_el and away_el):
                continue
            home = known.get(_norm(_clean_team(home_el.get_text(" ", strip=True))))
            away = known.get(_norm(_clean_team(away_el.get_text(" ", strip=True))))
            if not home or not away:
                continue  # descarta cruces de eliminatorias aun sin equipo definido

            m = MATCH_SCORE_RE.search(score_el.get_text(" ", strip=True))
            if m:
                hg, ag, status = int(m.group(1)), int(m.group(2)), "FINISHED"
            else:
                hg, ag, status = None, None, "SCHEDULED"

            utc = _parse_kickoff(b.get_text(" ", strip=True))

            out.append({
                "ext_id": f"wcm-{home}-{away}".replace(" ", "_"),
                "utc_date": utc, "stage": "GROUP_STAGE", "grp": None,
                "home": home, "away": away,
                "home_goals": hg, "away_goals": ag,
                "status": status, "source": "wikipedia-match",
            })
        if out:
            print(f"[wiki] {len(out)} partidos reales extraidos")
            return out
    return []
