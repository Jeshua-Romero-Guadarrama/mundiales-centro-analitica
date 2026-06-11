# =============================================================================
#  Mundial 2026 - Centro de Analitica
#  Autor: Jeshua Romero Guadarrama
# =============================================================================
"""Adaptador de scraping de Wikipedia: clasificaciones y resultados del torneo."""
from __future__ import annotations

import re

from ...core.config import WIKI_URLS
from .. import http

SCORE_RE = re.compile(r"^\s*(\d+)\s*[-–:]\s*(\d+)\s*$")


def _download(url: str) -> str | None:
    try:
        r = http.get(url, timeout=25)
        r.raise_for_status()
        r.encoding = "utf-8"  # Wikipedia siempre es UTF-8
        return r.text
    except Exception as exc:
        print(f"[wiki] descarga fallida {url}: {exc}")
        return None


def _clean(name: str) -> str:
    return re.sub(r"\[.*?\]", "", name).strip()


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


def fetch_results() -> list[dict]:
    """Partidos FINALIZADOS detectados en las tablas de Wikipedia."""
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

        results: list[dict] = []
        for tbl in tables:
            cols = [str(c) for c in tbl.columns]
            if not any(re.search(r"score|resultado", c, re.I) for c in cols):
                continue
            for _, row in tbl.iterrows():
                cells = [str(v).strip() for v in row.tolist()]
                for i, cell in enumerate(cells):
                    m = SCORE_RE.match(cell)
                    if m and i >= 1 and i + 1 < len(cells):
                        home, away = cells[i - 1], cells[i + 1]
                        if not home or not away or "nan" in (home, away):
                            continue
                        results.append({
                            "ext_id": f"wiki-{home}-{away}".replace(" ", "_"),
                            "utc_date": None, "stage": None, "grp": None,
                            "home": _clean(home), "away": _clean(away),
                            "home_goals": int(m.group(1)),
                            "away_goals": int(m.group(2)),
                            "status": "FINISHED", "source": "wikipedia",
                        })
        if results:
            print(f"[wiki] {len(results)} resultados extraidos")
            return results
    return []
