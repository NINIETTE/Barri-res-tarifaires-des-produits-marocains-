#!/usr/bin/env python3
"""
Test de reproductibilité du pipeline réel.

Vérifie que les fichiers produits par le pipeline existent et que leurs
caractéristiques correspondent à ce que le rapport affirme. Aucune valeur
n'est comparée à un chiffre codé en dur qui ne serait pas justifié par une
source : on teste des invariants structurels et des bornes, pas des résultats
exacts (qui peuvent bouger si les APIs mettent à jour leurs données).

Usage : venv/bin/python scripts/test_reproductibilite.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed" / "dataset_merged.csv"
RESULTS = ROOT / "data" / "processed" / "resultats_modeles.csv"
ELAST = ROOT / "data" / "processed" / "elasticite_tarifaire.json"
FIGURES = ROOT / "figures"
NOTEBOOK = ROOT / "notebooks" / "analyse_barrieres_tarifaires_maroc.ipynb"

failures: list[str] = []


def check(condition: bool, message: str, detail: str = "") -> None:
    if condition:
        print(f"  OK    {message}")
    else:
        print(f"  ÉCHEC {message}")
        if detail:
            print(f"        {detail}")
        failures.append(message)


def header(title: str) -> None:
    print("\n" + "=" * 74)
    print(title)
    print("=" * 74)


def main() -> int:
    header("1. Dataset fusionné")
    if not DATA.exists():
        check(False, "dataset_merged.csv existe",
              "Lancer scripts/build_dataset.py")
        return summary()
    df = pd.read_csv(DATA, dtype={"cmdCode": str})
    check(True, f"dataset_merged.csv chargé : {df.shape[0]} × {df.shape[1]}")
    check(len(df) > 400, "au moins 400 observations",
          f"obtenu : {len(df)}")
    check(df["cmdCode"].unique().tolist() == ["0702"],
          "cmdCode vaut bien '0702' (zéro initial préservé)",
          f"obtenu : {df['cmdCode'].unique().tolist()}")
    check(df["reporterCode"].unique().tolist() == [504],
          "reporterCode = 504 (Maroc)")
    check(df["flowCode"].unique().tolist() == ["X"],
          "flowCode = X (exportations)")
    check(df["period"].min() == 2010 and df["period"].max() == 2023,
          "période 2010-2023")
    check(df.duplicated(subset=["period", "partnerCode"]).sum() == 0,
          "aucun doublon (partenaire, année)")
    check((df["primaryValue"] > 0).all(), "toutes les valeurs sont > 0")

    # Couverture des sources
    header("2. Couverture des quatre sources")
    n = len(df)
    for col, label, mini in [
        ("gdp_partner_usd", "PIB (Banque mondiale)", 0.80),
        ("distance_km_cepii", "distance (CEPII)", 0.90),
        ("tariff_npf_pct", "droit NPF (WITS)", 0.40),
    ]:
        if col not in df.columns:
            check(False, f"{label} présent dans le dataset")
            continue
        taux = df[col].notna().mean()
        check(taux >= mini, f"{label} : {taux * 100:.1f} % renseigné",
              f"seuil attendu >= {mini * 100:.0f} %")

    if "tariff_npf_pct" in df.columns:
        sub = df.dropna(subset=["tariff_npf_pct"])
        part = sub["primaryValue"].sum() / df["primaryValue"].sum()
        check(part > 0.90,
              f"les obs. tarifaires couvrent {part * 100:.1f} % de la valeur",
              "seuil attendu > 90 %")

    # Cohérence temporelle de la croissance
    header("3. Cohérence du taux de croissance")
    if "growth_rate_pct" in df.columns:
        bad = df[(df["growth_rate_pct"].notna()) &
                 (df["intervalle_annees"] != 1)]
        check(len(bad) == 0,
              "growth_rate_pct n'est calculé que sur des années consécutives",
              f"{len(bad)} lignes calculées sur un intervalle irrégulier")

        # Les très fortes croissances doivent s'expliquer par une base minuscule
        # (ex. Japon 2012 : 10 USD -> 2013 : 10 848 USD = +108 380 %).
        # On ne les supprime pas : ce sont de vrais flux. On vérifie qu'elles
        # ne sont pas des erreurs de calcul.
        grosses = df[df["growth_rate_pct"].abs() > 1000]
        if len(grosses):
            base_faible = (grosses["lag_value"] < 250_000).all()
            check(base_faible,
                  f"les {len(grosses)} croissances > 1000 % ont toutes une base "
                  f"< 250 000 USD (vrais petits flux, pas des erreurs)",
                  f"base max = {grosses['lag_value'].max():,.0f} USD")

        # Vérification arithmétique : la formule doit être exacte
        calc = df[df["growth_rate_pct"].notna()].copy()
        attendu = ((calc["primaryValue"] - calc["lag_value"])
                   / calc["lag_value"] * 100)
        ecart = (calc["growth_rate_pct"] - attendu).abs().max()
        check(ecart < 1e-6,
              "growth_rate_pct correspond exactement à la formule documentée",
              f"écart max = {ecart:.2e}")

    # Résultats de modélisation
    header("4. Résultats de modélisation")
    if RESULTS.exists():
        res = pd.read_csv(RESULTS)
        check(len(res) == 4, f"4 modèles comparés (obtenu : {len(res)})")
        check("R2" in res.columns, "colonne R2 présente")
        baseline = res[res["modele"].str.contains("Baseline", na=False)]
        check(len(baseline) == 1, "la baseline figure dans le tableau")
        if len(baseline) == 1:
            check(baseline["R2"].iloc[0] < 0.1,
                  "la baseline a un R² proche de 0 (référence naïve)",
                  f"obtenu : {baseline['R2'].iloc[0]:.3f}")
        best = res.loc[res["R2"].idxmax()]
        check(best["R2"] > 0,
              f"le meilleur modèle explique une part positive : "
              f"{best['modele']} R²={best['R2']:.3f}")
        check(best["R2"] < 0.95,
              "aucun modèle n'affiche un R² invraisemblable (> 0,95)",
              f"obtenu : {best['R2']:.3f}")
    else:
        check(False, "resultats_modeles.csv existe",
              "Lancer scripts/modelisation.py")

    header("5. Élasticité tarifaire")
    if ELAST.exists():
        el = json.loads(ELAST.read_text(encoding="utf-8"))
        if "coef_log_tariff" in el:
            check(True, f"coefficient estimé : {el['coef_log_tariff']:+.3f} "
                        f"[{el['ic95_bas']:+.3f} ; {el['ic95_haut']:+.3f}]")
            check(el["n_observations"] >= 20,
                  f"effectif suffisant : n = {el['n_observations']}")
            check(el["se"] is not None, "erreur standard calculée")
            check("interpretation" in el and len(el["interpretation"]) > 50,
                  "interprétation documentée")
            # Le rapport doit signaler que le signe peut être contre-intuitif
            check("NPF" in el["interpretation"],
                  "l'interprétation mentionne la limite NPF")
        else:
            check(False, "coefficient présent", str(el))
    else:
        check(False, "elasticite_tarifaire.json existe")

    header("6. Figures")
    expected = [
        "fig1_evolution_temporelle.png",
        "fig2_top10_destinations.png",
        "fig3_correlation_tarifs.png",
        "fig4_distribution_tarifs.png",
        "fig5_series_temporelles.png",
        "fig6_validation_modeles.png",
    ]
    for fig in expected:
        p = FIGURES / fig
        check(p.exists() and p.stat().st_size > 10_000,
              f"{fig} ({p.stat().st_size // 1024} Ko)" if p.exists()
              else f"{fig} manquante")

    header("7. Notebook exécuté")
    if NOTEBOOK.exists():
        nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
        code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
        executed = [c for c in code_cells if c.get("execution_count")]
        errors = [
            o for c in code_cells for o in c.get("outputs", [])
            if o.get("output_type") == "error"
        ]
        check(len(executed) == len(code_cells),
              f"toutes les cellules code exécutées "
              f"({len(executed)}/{len(code_cells)})")
        check(len(errors) == 0, "aucune erreur dans les sorties",
              f"{len(errors)} erreur(s)")
    else:
        check(False, "notebook principal présent")

    header("8. Rapport LaTeX")
    tex = ROOT / "rapport" / "rapport.tex"
    pdf = ROOT / "rapport" / "rapport.pdf"
    check(tex.exists(), "rapport.tex existe")
    check(pdf.exists() and pdf.stat().st_size > 100_000,
          f"rapport.pdf compilé ({pdf.stat().st_size // 1024} Ko)"
          if pdf.exists() else "rapport.pdf manquant")
    if tex.exists():
        content = tex.read_text(encoding="utf-8")
        check("À compléter" not in content,
              "aucun marqueur [À compléter] restant")
        check("Hiba Yacoubi" in content and "Meriem Ninia" in content,
              "noms du binôme renseignés")
        check(content.count("includegraphics") >= 6,
              f"{content.count('includegraphics')} figures incluses")
        log = ROOT / "rapport" / "rapport.log"
        if log.exists():
            txt = log.read_text(encoding="utf-8", errors="replace")
            check(txt.count("Overfull") == 0,
                  "aucun débordement horizontal/vertical dans rapport.log",
                  f"{txt.count('Overfull')} avertissement(s) Overfull")

    header("9. Soutenance")
    s_tex = ROOT / "soutenance" / "soutenance.tex"
    s_pdf = ROOT / "soutenance" / "soutenance.pdf"
    check(s_tex.exists(), "soutenance.tex existe")
    check(s_pdf.exists() and s_pdf.stat().st_size > 50_000,
          f"soutenance.pdf compilé ({s_pdf.stat().st_size // 1024} Ko)"
          if s_pdf.exists() else "soutenance.pdf manquant")
    if s_tex.exists():
        content = s_tex.read_text(encoding="utf-8")
        check("À compléter" not in content, "aucun marqueur restant")
        check("0{,}891" not in content,
              "aucun chiffre de la version simulée (R²=0,891)")
        s_log = ROOT / "soutenance" / "soutenance.log"
        if s_log.exists():
            txt = s_log.read_text(encoding="utf-8", errors="replace")
            check(txt.count("Overfull") == 0,
                  "aucun débordement de diapositive dans soutenance.log",
                  f"{txt.count('Overfull')} avertissement(s) Overfull")

    return summary()


def summary() -> int:
    print("\n" + "=" * 74)
    if failures:
        print(f"{len(failures)} ÉCHEC(S)")
        for f in failures:
            print(f"  - {f}")
        print("=" * 74)
        return 1
    print("TOUS LES TESTS PASSENT")
    print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
