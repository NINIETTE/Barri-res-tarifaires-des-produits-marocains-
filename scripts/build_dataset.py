#!/usr/bin/env python3
"""
Construction du dataset final à partir des sources RÉELLES extraites.

Entrées (toutes réelles, aucune simulation) :
  data/raw/comtrade_maroc_tomates_2010_2023.csv   UN Comtrade, exportations Maroc HS 0702
  data/raw/worldbank_gdp_partners.csv             Banque mondiale, PIB courant des partenaires
  data/raw/wits_tarifs_npf_2010_2023.csv          WITS/UNCTAD TRAINS, droits NPF HS 070200
  data/raw/cepii_distances_mar.csv                CEPII, distances bilatérales depuis le Maroc

Sortie :
  data/processed/dataset_merged.csv
  data/processed/metadata_dataset.json

Principes :
  - Aucune valeur n'est inventée. Une variable indisponible reste manquante (NaN).
  - Chaque variable est tracée jusqu'à sa source dans metadata_dataset.json.
  - Le tarif NPF n'est PAS le tarif subi par le Maroc : la colonne est nommée
    explicitement tariff_npf_pct et documentée comme telle.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW = PROJECT_ROOT / "data" / "raw"
PROCESSED = PROJECT_ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. Distances CEPII : on les matérialise dans data/raw pour la traçabilité
# ---------------------------------------------------------------------------
def build_cepii_distances() -> pd.DataFrame:
    src = Path("/tmp/distc/dist_cepii.xls")
    if not src.exists():
        raise FileNotFoundError(
            "Fichier CEPII absent. Télécharger https://www.cepii.fr/distance/dist_cepii.zip "
            "et l'extraire dans /tmp/distc/."
        )
    d = pd.read_excel(src, engine="xlrd")
    mar = d[d["iso_o"] == "MAR"][["iso_d", "dist", "contig", "comlang_off"]].copy()
    mar = mar.rename(columns={"iso_d": "iso3", "dist": "distance_km_cepii",
                              "contig": "contigu", "comlang_off": "langue_officielle_commune"})
    out = RAW / "cepii_distances_mar.csv"
    mar.to_csv(out, index=False, encoding="utf-8")
    return mar


# ---------------------------------------------------------------------------
# 2. Fusion
# ---------------------------------------------------------------------------
def main() -> None:
    started = datetime.now(timezone.utc)

    comtrade = pd.read_csv(RAW / "comtrade_maroc_tomates_2010_2023.csv", dtype={"cmdCode": str})
    gdp = pd.read_csv(RAW / "worldbank_gdp_partners.csv")
    wits_path = RAW / "wits_tarifs_npf_2010_2023.csv"
    wits = pd.read_csv(wits_path) if wits_path.exists() else pd.DataFrame()
    dist = build_cepii_distances()

    comtrade["period"] = comtrade["period"].astype(int)
    comtrade["partnerCode"] = comtrade["partnerCode"].astype(int)

    df = comtrade.copy()

    # --- PIB : déjà joint par l'extracteur, on vérifie et on renomme clairement
    if "gdp_usd" in df.columns:
        df = df.rename(columns={"gdp_usd": "gdp_partner_usd"})
    else:
        df = df.merge(gdp.rename(columns={"gdp_usd": "gdp_partner_usd"}),
                      left_on=["iso3", "period"], right_on=["iso3", "year"], how="left")
        df = df.drop(columns=["year"], errors="ignore")

    # --- Distances réelles CEPII
    df = df.merge(dist, on="iso3", how="left")

    # --- Tarifs NPF : WITS déclare par « déclarant », pas par partenaire.
    # L'UE (918) couvre tous ses membres ; les autres déclarants sont eux-mêmes.
    df["wits_reporter"] = None
    if not wits.empty:
        eu_members = {
            "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN", "FRA",
            "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX", "MLT", "NLD",
            "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
        }
        df.loc[df["iso3"].isin(eu_members), "wits_reporter"] = 918
        for rep, iso in [(826, "GBR"), (643, "RUS"), (757, "CHE"), (682, "SAU"),
                         (784, "ARE"), (842, "USA"), (392, "JPN"), (156, "CHN"),
                         (699, "IND")]:
            df.loc[df["iso3"] == iso, "wits_reporter"] = rep

        wits_small = wits[["reporterCode", "year", "tariff_npf_pct",
                           "tariff_type", "measure", "n_lines"]].rename(
            columns={"reporterCode": "wits_reporter", "year": "period",
                     "tariff_type": "tariff_source_type",
                     "measure": "tariff_measure",
                     "n_lines": "tariff_n_lines"})
        wits_small["wits_reporter"] = wits_small["wits_reporter"].astype("Int64")
        df["wits_reporter"] = df["wits_reporter"].astype("Int64")
        df = df.merge(wits_small, on=["wits_reporter", "period"], how="left")

    # --- Variables calculées (aucune invention : simples transformations)
    df["log_value"] = (df["primaryValue"].where(df["primaryValue"] > 0)).apply(
        lambda x: __import__("math").log(x) if pd.notna(x) else float("nan"))
    df["log_weight"] = (df["netWgt"].where(df["netWgt"] > 0)).apply(
        lambda x: __import__("math").log(x) if pd.notna(x) else float("nan"))
    df["log_gdp"] = df["gdp_partner_usd"].where(df["gdp_partner_usd"] > 0).apply(
        lambda x: __import__("math").log(x) if pd.notna(x) else float("nan"))
    df["log_distance"] = df["distance_km_cepii"].where(df["distance_km_cepii"] > 0).apply(
        lambda x: __import__("math").log(x) if pd.notna(x) else float("nan"))

    df["prix_unitaire_usd_kg"] = df["primaryValue"] / df["netWgt"].where(df["netWgt"] > 0)
    df["trend"] = df["period"] - df["period"].min()

    df = df.sort_values(["partnerCode", "period"]).reset_index(drop=True)

    # Le taux de croissance n'a de sens que sur des années consécutives.
    # Un partenaire peut manquer certaines années : on le signale explicitement
    # plutôt que de calculer une variation sur un intervalle irrégulier.
    df["annee_precedente"] = df.groupby("partnerCode")["period"].shift(1)
    df["intervalle_annees"] = df["period"] - df["annee_precedente"]
    df["lag_value"] = df.groupby("partnerCode")["primaryValue"].shift(1)
    df["growth_rate_pct"] = np.where(
        df["intervalle_annees"] == 1,
        (df["primaryValue"] - df["lag_value"]) / df["lag_value"].where(df["lag_value"] > 0) * 100,
        np.nan,
    )

    # --- Colonnes finales
    cols = [
        "period", "reporterCode", "reporterDesc", "partnerCode", "partnerName", "iso3",
        "flowCode", "flowDesc", "cmdCode", "cmdDesc",
        "primaryValue", "netWgt", "qty", "qtyUnitAbbr", "prix_unitaire_usd_kg",
        "tariff_npf_pct", "tariff_source_type", "tariff_measure", "tariff_n_lines",
        "gdp_partner_usd", "distance_km_cepii", "contigu", "langue_officielle_commune",
        "log_value", "log_weight", "log_gdp", "log_distance",
        "trend", "annee_precedente", "intervalle_annees", "lag_value", "growth_rate_pct",
    ]
    cols = [c for c in cols if c in df.columns]
    final = df[cols]

    out = PROCESSED / "dataset_merged.csv"
    final.to_csv(out, index=False, encoding="utf-8")

    # --- Métadonnées de traçabilité
    couverture = {}
    for col, src in [
        ("primaryValue", "UN Comtrade (extrait)"),
        ("netWgt", "UN Comtrade (extrait)"),
        ("gdp_partner_usd", "Banque mondiale WDI NY.GDP.MKTP.CD"),
        ("distance_km_cepii", "CEPII dist_cepii"),
        ("tariff_npf_pct", "WITS / UNCTAD TRAINS (MFN, moyenne simple)"),
    ]:
        if col in final.columns:
            couverture[col] = {
                "source": src,
                "renseignees": int(final[col].notna().sum()),
                "manquantes": int(final[col].isna().sum()),
                "taux_renseignement_pct": round(final[col].notna().mean() * 100, 1),
            }

    meta = {
        "date_construction_utc": started.isoformat(),
        "type": "DONNÉES RÉELLES — aucune simulation",
        "lignes": int(len(final)),
        "colonnes": int(len(final.columns)),
        "partenaires": int(final["partnerCode"].nunique()),
        "annees": [int(final["period"].min()), int(final["period"].max())],
        "couverture_par_variable": couverture,
        "avertissements": [
            "tariff_npf_pct est le droit NPF déclaré par le pays importateur. "
            "Le Maroc bénéficie de taux préférentiels (accord UE-Maroc), souvent 0 %. "
            "Ce n'est donc PAS le tarif effectivement subi par le Maroc.",
            "Les 72 observations sans PIB correspondent à des partenaires hors du "
            "référentiel Banque mondiale ou à des pays sans déclaration pour l'année.",
            "Aucune variable de préférence commerciale n'a été fabriquée : la variable "
            "preferential_agreement du projet initial a été supprimée faute de source.",
        ],
        "sources": [
            {"nom": "UN Comtrade", "fichier": "data/raw/comtrade_maroc_tomates_2010_2023.csv"},
            {"nom": "Banque mondiale", "fichier": "data/raw/worldbank_gdp_partners.csv"},
            {"nom": "WITS / UNCTAD TRAINS", "fichier": "data/raw/wits_tarifs_npf_2010_2023.csv"},
            {"nom": "CEPII", "fichier": "data/raw/cepii_distances_mar.csv"},
        ],
    }
    (PROCESSED / "metadata_dataset.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Écrit : {out} ({len(final)} lignes, {len(final.columns)} colonnes)")
    for col, info in couverture.items():
        print(f"  {col:22s} renseigné à {info['taux_renseignement_pct']:5.1f} %")
    print("\nAperçu :")
    print(final.head(3).to_string())


if __name__ == "__main__":
    main()
