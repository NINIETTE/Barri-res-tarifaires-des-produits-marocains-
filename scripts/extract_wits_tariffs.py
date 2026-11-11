#!/usr/bin/env python3
"""
Extraction des tarifs réels depuis l'API WITS (Banque mondiale / UNCTAD TRAINS).

Endpoint : https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/
           reporter/{code}/partner/000/product/070200/year/{annee}/datatype/reported

Ce que l'API renvoie réellement (vérifié le 2026-11-11) :
  - TARIFFTYPE = MFN                 -> droit NPF (Most Favoured Nation)
  - OBS_VALUE_MEASURE = SimpleAverage -> moyenne simple sur les lignes tarifaires HS6
  - partner/000 (monde) : l'API ne fournit PAS le taux préférentiel Maroc
    (partner/504 renvoie 404 pour la plupart des déclarants).

LIMITE IMPORTANTE ET DOCUMENTÉE :
Les valeurs extraites sont des taux NPF, pas les taux effectivement payés par le Maroc
(qui bénéficie de taux préférentiels, souvent 0 %, sous l'accord d'association UE-Maroc).
Le rapport doit présenter ces chiffres comme « tarif NPF déclaré par le pays importateur »,
jamais comme « tarif subi par le Maroc ».

WITS est lent (~40 s/réponse) : les requêtes sont lancées en parallèle et chaque réponse
est mise en cache dans data/raw/wits_cache/ pour rendre le script rejouable.

Sortie : data/raw/wits_tarifs_npf_2010_2023.csv
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CACHE_DIR = RAW_DIR / "wits_cache"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
for d in (RAW_DIR, CACHE_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

WITS = ("https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/"
        "reporter/{rep}/partner/000/product/070200/year/{year}/datatype/reported?format=JSON")

ANNEES = list(range(2010, 2024))

# Déclarants sélectionnés sur la valeur exportée réelle : les 5 premiers partenaires
# concentrent 94 % des exportations marocaines de tomates (France 66 %, Royaume-Uni 8 %,
# Espagne 6 %, Pays-Bas 6 %, Russie 5 %). L'UE partage un tarif commun, couvert par 918.
REPORTERS = {
    918: "European Union (agrégat)",
    826: "United Kingdom",
    643: "Russian Federation",
    757: "Switzerland",
    682: "Saudi Arabia",
    784: "United Arab Emirates",
    842: "United States",
    392: "Japan",
    156: "China",
    699: "India",
}

WORKERS = 20

LOGFILE = LOGS_DIR / f"wits_{datetime.now():%Y%m%d_%H%M%S}.log"


def log(msg: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    with open(LOGFILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def fetch(url: str, tries: int = 3) -> dict | None:
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "projet-academique/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = resp.read().decode("utf-8-sig")
            if not body.lstrip().startswith("{"):
                return None  # WITS renvoie du HTML quand la requête échoue
            return json.loads(body)
        except urllib.error.HTTPError as exc:
            if exc.code in (307, 404):
                return None
            time.sleep(10 * attempt)
        except Exception:
            time.sleep(10 * attempt)
    return None


def parse(payload: dict) -> dict | None:
    try:
        series = payload["dataSets"][0]["series"]
        if not series:
            return None
        obs = list(series.values())[0]["observations"]
        rate = list(obs.values())[0][0]
        attrs = {a["id"]: [v["id"] for v in a["values"]]
                 for a in payload["structure"]["attributes"]["observation"]}
        return {
            "tariff_npf_pct": rate,
            "tariff_type": (attrs.get("TARIFFTYPE") or [None])[0],
            "measure": (attrs.get("OBS_VALUE_MEASURE") or [None])[0],
            "nomenclature": (attrs.get("NOMENCODE") or [None])[0],
            "n_lines": (attrs.get("TOTALNOOFLINES") or [None])[0],
            "min_rate": (attrs.get("MIN_RATE") or [None])[0],
            "max_rate": (attrs.get("MAX_RATE") or [None])[0],
        }
    except Exception:
        return None


def job(rep: int, name: str, year: int) -> tuple[int, str, int, dict | None]:
    cache = CACHE_DIR / f"wits_{rep}_{year}.json"
    if cache.exists():
        raw = json.loads(cache.read_text(encoding="utf-8"))
        return rep, name, year, raw
    payload = fetch(WITS.format(rep=rep, year=year))
    cache.write_text(json.dumps(payload, ensure_ascii=False) if payload else "null",
                     encoding="utf-8")
    return rep, name, year, payload


def main() -> None:
    started = datetime.now(timezone.utc)
    log("=" * 70)
    log("EXTRACTION TARIFS NPF — WITS / UNCTAD TRAINS — HS 070200")
    log(f"{len(REPORTERS)} déclarants x {len(ANNEES)} années, {WORKERS} requêtes en parallèle")
    log("=" * 70)

    tasks = [(rep, name, y) for rep, name in REPORTERS.items() for y in ANNEES]
    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(job, *t) for t in tasks]
        for fut in as_completed(futures):
            rep, name, year, payload = fut.result()
            done += 1
            rec = parse(payload) if payload else None
            if rec is None:
                log(f"[{done}/{len(tasks)}] {name:26s} {year} : aucune donnée")
                continue
            rec.update({"reporterCode": rep, "reporterName": name, "year": year})
            rows.append(rec)
            log(f"[{done}/{len(tasks)}] {name:26s} {year} : "
                f"{rec['tariff_npf_pct']:.2f} % ({rec['tariff_type']}, {rec['measure']})")

    df = pd.DataFrame(rows)
    if df.empty:
        log("AUCUNE donnée tarifaire récupérée.")
        return

    df = df[["reporterCode", "reporterName", "year", "tariff_npf_pct",
             "tariff_type", "measure", "nomenclature", "n_lines",
             "min_rate", "max_rate"]].sort_values(["reporterCode", "year"])

    out = RAW_DIR / "wits_tarifs_npf_2010_2023.csv"
    df.to_csv(out, index=False, encoding="utf-8")
    log(f"Écrit : {out} ({len(df)} lignes)")

    meta = {
        "date_extraction_utc": started.isoformat(),
        "source": "WITS — Banque mondiale / UNCTAD TRAINS",
        "endpoint": WITS,
        "produit": "HS 070200 (tomates fraîches ou réfrigérées)",
        "type_tarif": "MFN (droit NPF) — moyenne simple",
        "declarants": {str(k): v for k, v in REPORTERS.items()},
        "lignes": int(len(df)),
        "annees": [int(df["year"].min()), int(df["year"].max())],
        "avertissement": (
            "Ces taux sont les droits NPF déclarés par le pays importateur. "
            "Le Maroc bénéficie de taux préférentiels (accord UE-Maroc), souvent 0 %. "
            "WITS ne fournit pas le taux préférentiel Maroc (partner/504 -> 404). "
            "Ces valeurs ne doivent donc PAS être présentées comme le tarif subi par le Maroc."
        ),
    }
    (RAW_DIR / "metadata_wits.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    log("Terminé.")


if __name__ == "__main__":
    main()
