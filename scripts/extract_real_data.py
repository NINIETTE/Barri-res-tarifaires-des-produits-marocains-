#!/usr/bin/env python3
"""
Extraction des DONNÉES RÉELLES pour le projet « Barrières tarifaires ».

Sources effectivement appelées :
  1. UN Comtrade — API publique preview, exportations Maroc (504) HS 0702, 2010-2023,
     ventilées par pays partenaire.
     URL : https://comtradeapi.un.org/public/v1/preview/C/A/HS
  2. Banque mondiale — API Indicators, PIB courant (NY.GDP.MKTP.CD) des partenaires.
     URL : https://api.worldbank.org/v2/country/{ISO3}/indicator/NY.GDP.MKTP.CD

Chaque réponse brute est mise en cache dans data/raw/api_cache/ afin que le script
soit rejouable sans re-solliciter les serveurs (reproductibilité J13).

Sorties :
  data/raw/comtrade_maroc_tomates_2010_2023.csv   (observations réelles, une ligne/partenaire/année)
  data/raw/worldbank_gdp_partners.csv             (PIB réel par partenaire et par année)
  data/raw/metadata_extraction.json               (traçabilité : URL, date, compteurs, licence)
  data/logs/extraction_<horodatage>.log           (journal complet des appels)
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CACHE_DIR = RAW_DIR / "api_cache"
LOGS_DIR = PROJECT_ROOT / "data" / "logs"
for d in (RAW_DIR, CACHE_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

COMTRADE_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
COMTRADE_REF_URL = "https://comtradeapi.un.org/files/v1/app/reference/Reporters.json"
WORLDBANK_URL = "https://api.worldbank.org/v2/country/{iso3}/indicator/NY.GDP.MKTP.CD"

REPORTER_MAROC = 504
HS_TOMATES = "0702"
ANNEES = list(range(2010, 2024))

# Correspondance code partenaire Comtrade -> ISO3, pour interroger la Banque mondiale.
# Seuls les partenaires effectivement présents dans les données Comtrade seront utilisés ;
# les codes absents de cette table sont conservés mais sans PIB (valeur manquante, non inventée).
CODE_TO_ISO3 = {
    251: "FRA", 276: "DEU", 724: "ESP", 826: "GBR", 528: "NLD",
    56: "BEL", 380: "ITA", 616: "POL", 643: "RUS", 842: "USA",
    620: "PRT", 208: "DNK", 752: "SWE", 246: "FIN", 372: "IRL",
    40: "AUT", 300: "GRC", 203: "CZE", 348: "HUN", 703: "SVK",
    705: "SVN", 100: "BGR", 642: "ROU", 191: "HRV", 440: "LTU",
    428: "LVA", 233: "EST", 470: "MLT", 196: "CYP", 442: "LUX",
    392: "JPN", 410: "KOR", 156: "CHN", 356: "IND", 36: "AUS",
    124: "CAN", 756: "CHE", 578: "NOR", 784: "ARE", 682: "SAU",
    634: "QAT", 414: "KWT", 48: "BHR", 512: "OMN", 788: "TUN",
    12: "DZA", 818: "EGY", 504: "MAR", 364: "IRN", 792: "TUR",
    376: "ISR", 152: "CHL", 76: "BRA", 484: "MEX", 710: "ZAF",
    458: "MYS", 764: "THA", 360: "IDN", 608: "PHL", 704: "VNM",
    398: "KAZ", 804: "UKR", 112: "BLR", 688: "SRB", 807: "MKD",
    8: "ALB", 499: "MNE", 70: "BIH", 268: "GEO", 51: "ARM",
    31: "AZE", 860: "UZB", 496: "MNG", 144: "LKA", 586: "PAK",
    50: "BGD", 524: "NPL", 116: "KHM", 104: "MMR", 231: "ETH",
    404: "KEN", 834: "TZA", 800: "UGA", 288: "GHA", 566: "NGA",
    384: "CIV", 686: "SEN", 466: "MLI", 854: "BFA", 562: "NER",
    148: "TCD", 120: "CMR", 178: "COG", 180: "COD", 24: "AGO",
    508: "MOZ", 716: "ZWE", 894: "ZMB", 454: "MWI", 516: "NAM",
    72: "BWA", 748: "SWZ", 426: "LSO", 132: "CPV", 624: "GNB",
    270: "GMB", 324: "GIN", 694: "SLE", 430: "LBR", 204: "BEN",
    768: "TGO", 288: "GHA", 232: "ERI", 262: "DJI", 706: "SOM",
    728: "SSD", 729: "SDN", 434: "LBY", 760: "SYR", 400: "JOR",
    422: "LBN", 368: "IRQ", 887: "YEM", 4: "AFG", 764: "THA",
}

LOGFILE = LOGS_DIR / f"extraction_{datetime.now():%Y%m%d_%H%M%S}.log"


def log(msg: str) -> None:
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOGFILE, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def http_json(url: str, tries: int = 6, base_sleep: float = 5.0) -> dict | list:
    """GET JSON avec backoff exponentiel sur 429/5xx."""
    last = None
    for attempt in range(1, tries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "projet-academique/1.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 500, 502, 503, 504):
                wait = base_sleep * (2 ** (attempt - 1))
                log(f"    HTTP {exc.code} — attente {wait:.0f}s (essai {attempt}/{tries})")
                time.sleep(wait)
                continue
            raise
        except Exception as exc:  # réseau
            last = exc
            wait = base_sleep * (2 ** (attempt - 1))
            log(f"    {type(exc).__name__} — attente {wait:.0f}s (essai {attempt}/{tries})")
            time.sleep(wait)
    raise RuntimeError(f"Échec après {tries} essais : {last}")


# ----------------------------------------------------------------------------
# 0. Référentiel officiel Comtrade — noms de pays et codes ISO3
# ----------------------------------------------------------------------------
def fetch_reference() -> pd.DataFrame:
    """L'endpoint preview renvoie partnerDesc=null : on récupère le référentiel officiel."""
    log("PHASE 0 — Référentiel Comtrade (codes pays -> noms et ISO3)")
    cache = CACHE_DIR / "comtrade_reporters_reference.json"
    if cache.exists():
        payload = json.loads(cache.read_text(encoding="utf-8"))
        log("Cache local réutilisé")
    else:
        log(f"GET {COMTRADE_REF_URL}")
        payload = http_json(COMTRADE_REF_URL)
        cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        time.sleep(2)

    ref = pd.DataFrame(payload["results"])
    ref = ref.rename(columns={"id": "partnerCode", "text": "partnerName",
                              "reporterCodeIsoAlpha3": "iso3_ref"})
    ref["partnerCode"] = ref["partnerCode"].astype(int)
    log(f"{len(ref)} codes pays dans le référentiel")
    return ref[["partnerCode", "partnerName", "iso3_ref"]]


# ----------------------------------------------------------------------------
# 1. UN Comtrade — exportations marocaines HS 0702 par partenaire
# ----------------------------------------------------------------------------
def fetch_comtrade() -> pd.DataFrame:
    log("=" * 70)
    log("PHASE 1 — UN Comtrade : exportations Maroc HS 0702 (2010-2023)")
    log(f"Endpoint : {COMTRADE_URL}")
    log("=" * 70)

    frames, appels = [], 0
    for year in ANNEES:
        cache = CACHE_DIR / f"comtrade_504_0702_X_{year}.json"
        if cache.exists():
            payload = json.loads(cache.read_text(encoding="utf-8"))
            log(f"{year} : cache local réutilisé")
        else:
            params = {
                "reporterCode": REPORTER_MAROC,
                "partnerCode": "",      # tous les partenaires
                "cmdCode": HS_TOMATES,
                "flowCode": "X",
                "period": str(year),
            }
            url = COMTRADE_URL + "?" + urllib.parse.urlencode(params)
            log(f"{year} : GET {url}")
            payload = http_json(url)
            cache.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            appels += 1
            time.sleep(3)  # respect du quota public

        rows = payload.get("data", [])
        if not rows:
            log(f"{year} : AUCUNE donnée renvoyée")
            continue

        df_year = pd.DataFrame(rows)
        # On conserve le total agrégé (partnerCode 0) ET le détail par partenaire ;
        # le total servira de contrôle de cohérence.
        frames.append(df_year)
        log(f"{year} : {len(df_year)} lignes ({df_year['partnerCode'].nunique()} partenaires)")

    if not frames:
        raise RuntimeError("Comtrade n'a renvoyé aucune donnée.")

    raw = pd.concat(frames, ignore_index=True)
    log(f"Total brut : {len(raw)} lignes, {len(raw.columns)} colonnes")

    keep = [
        "period", "reporterCode", "reporterDesc", "partnerCode", "partnerDesc",
        "flowCode", "flowDesc", "cmdCode", "cmdDesc", "primaryValue",
        "netWgt", "qty", "qtyUnitAbbr", "cifvalue", "fobvalue",
        "isAggregate", "isReported", "classificationCode",
    ]
    keep = [c for c in keep if c in raw.columns]
    df = raw[keep].copy()

    # Ne garder que les observations réelles déclarées, hors ligne « World » (partnerCode 0)
    df = df[df["partnerCode"] != 0].copy()
    df = df[df["primaryValue"].notna() & (df["primaryValue"] > 0)].copy()

    df = df.sort_values(["period", "primaryValue"], ascending=[True, False]).reset_index(drop=True)
    log(f"Après filtrage (hors total monde, valeurs > 0) : {len(df)} observations")
    log(f"Partenaires distincts : {df['partnerCode'].nunique()}")
    return df, appels


# ----------------------------------------------------------------------------
# 2. Banque mondiale — PIB courant des partenaires
# ----------------------------------------------------------------------------
def fetch_worldbank(codes: list[int]) -> pd.DataFrame:
    log("=" * 70)
    log("PHASE 2 — Banque mondiale : PIB courant des partenaires")
    log("=" * 70)

    iso3 = sorted({CODE_TO_ISO3[c] for c in codes if c in CODE_TO_ISO3})
    log(f"Pays interrogés ({len(iso3)}) : {', '.join(iso3)}")

    cache = CACHE_DIR / "worldbank_gdp.json"
    if cache.exists():
        log("Cache local réutilisé")
        payload = json.loads(cache.read_text(encoding="utf-8"))
    else:
        frames = []
        # L'API accepte plusieurs pays séparés par ';' mais limite la réponse :
        # on interroge par lots de 12.
        for i in range(0, len(iso3), 12):
            lot = ";".join(iso3[i:i + 12])
            url = (
                "https://api.worldbank.org/v2/country/"
                f"{lot}/indicator/NY.GDP.MKTP.CD"
                "?format=json&date=2010:2023&per_page=5000"
            )
            log(f"GET {url}")
            payload = http_json(url)
            frames.append(payload)
            time.sleep(1)
        cache.write_text(json.dumps(frames, ensure_ascii=False), encoding="utf-8")

    if isinstance(payload, dict):
        payload = [payload]

    records = []
    for page in payload:
        if not isinstance(page, list) or len(page) < 2 or page[1] is None:
            continue
        for row in page[1]:
            records.append({
                "iso3": row["countryiso3code"],
                "country": row["country"]["value"],
                "year": int(row["date"]),
                "gdp_usd": row["value"],
            })

    df = pd.DataFrame(records)
    df = df[df["gdp_usd"].notna()].copy()
    log(f"{len(df)} valeurs de PIB récupérées ({df['iso3'].nunique()} pays, "
        f"{df['year'].min()}-{df['year'].max()})")
    return df


def main() -> None:
    started = datetime.now(timezone.utc)
    log("DÉBUT EXTRACTION DONNÉES RÉELLES")
    log(f"Dossier projet : {PROJECT_ROOT}")

    reference = fetch_reference()
    comtrade, nb_appels = fetch_comtrade()
    codes = sorted(comtrade["partnerCode"].astype(int).unique().tolist())
    gdp = fetch_worldbank(codes)

    # Jointure du PIB réel sur (partenaire, année) — aucune valeur inventée
    comtrade["partnerCode"] = comtrade["partnerCode"].astype(int)
    comtrade["period"] = comtrade["period"].astype(int)

    # Noms officiels : le référentiel comble les partnerDesc null de l'endpoint preview
    comtrade = comtrade.drop(columns=["partnerDesc", "reporterDesc"], errors="ignore")
    comtrade = comtrade.merge(reference, on="partnerCode", how="left")
    comtrade["reporterDesc"] = "Morocco"
    comtrade["cmdDesc"] = "Tomatoes, fresh or chilled"
    comtrade["flowDesc"] = "Export"

    comtrade["iso3"] = comtrade["iso3_ref"].fillna(comtrade["partnerCode"].map(CODE_TO_ISO3))
    sans_nom = comtrade["partnerName"].isna().sum()
    if sans_nom:
        log(f"ATTENTION : {sans_nom} observations sans nom officiel "
            f"(codes {sorted(comtrade.loc[comtrade['partnerName'].isna(), 'partnerCode'].unique().tolist())})")

    merged = comtrade.merge(
        gdp, left_on=["iso3", "period"], right_on=["iso3", "year"], how="left"
    ).drop(columns=["year"])

    out_comtrade = RAW_DIR / "comtrade_maroc_tomates_2010_2023.csv"
    merged.to_csv(out_comtrade, index=False, encoding="utf-8")
    log(f"Écrit : {out_comtrade} ({len(merged)} lignes)")

    out_gdp = RAW_DIR / "worldbank_gdp_partners.csv"
    gdp.to_csv(out_gdp, index=False, encoding="utf-8")
    log(f"Écrit : {out_gdp} ({len(gdp)} lignes)")

    # Contrôle de cohérence : somme des partenaires vs total monde déclaré
    total_declare = None
    cache_total = CACHE_DIR / "comtrade_2010_2023_totaux.json"
    totaux = {}
    for year in ANNEES:
        f = CACHE_DIR / f"comtrade_504_0702_X_{year}.json"
        if not f.exists():
            continue
        payload = json.loads(f.read_text(encoding="utf-8"))
        agg = [r for r in payload.get("data", []) if r.get("partnerCode") == 0]
        if agg:
            totaux[str(year)] = agg[0]["primaryValue"]
    cache_total.write_text(json.dumps(totaux, indent=2), encoding="utf-8")

    metadata = {
        "date_extraction_utc": started.isoformat(),
        "type": "DONNÉES RÉELLES — extraites d'APIs publiques, aucune simulation",
        "sources": [
            {
                "nom": "UN Comtrade",
                "url": COMTRADE_URL,
                "parametres": {
                    "reporterCode": REPORTER_MAROC,
                    "cmdCode": HS_TOMATES,
                    "flowCode": "X",
                    "partnerCode": "tous",
                    "period": "2010-2023",
                },
                "licence": "Données publiques ONU, citées obligatoirement (UN Comtrade). "
                           "Endpoint preview : 500 lignes max par requête, sans clé.",
                "appels_http_effectues": nb_appels,
            },
            {
                "nom": "Banque mondiale — World Development Indicators",
                "url": "https://api.worldbank.org/v2/country/{iso3}/indicator/NY.GDP.MKTP.CD",
                "indicateur": "NY.GDP.MKTP.CD — PIB courant (USD)",
                "licence": "CC BY 4.0",
            },
        ],
        "nb_observations": int(len(merged)),
        "nb_annees": int(merged["period"].nunique()),
        "nb_partenaires": int(merged["partnerCode"].nunique()),
        "annees_couvertes": [int(merged["period"].min()), int(merged["period"].max())],
        "totaux_declares_par_comtrade_usd": totaux,
        "observations_sans_pib": int(merged["gdp_usd"].isna().sum()),
        "note": "Les variables tariff_rate, distance_km et preferential_agreement "
                "ne figurent PAS dans ce fichier : elles ne sont pas fournies par "
                "ces APIs et devront provenir de WITS/OMC et CEPII, ou être "
                "explicitement déclarées comme non disponibles.",
    }
    out_meta = RAW_DIR / "metadata_extraction.json"
    out_meta.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    log(f"Écrit : {out_meta}")
    log(f"FIN — {len(merged)} observations, {merged['partnerCode'].nunique()} partenaires, "
        f"{merged['period'].nunique()} années")
    log(f"Journal : {LOGFILE}")


if __name__ == "__main__":
    main()
