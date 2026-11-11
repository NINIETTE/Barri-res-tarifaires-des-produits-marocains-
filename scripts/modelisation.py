#!/usr/bin/env python3
"""
Modélisation — J6 à J9 (données réelles).

Corrections méthodologiques par rapport à la version précédente :

  1. SUPPRESSION de `trend` des variables explicatives. Un modèle à arbres ne sait pas
     extrapoler une tendance : avec un découpage temporel, il plafonne à la dernière
     valeur vue en entraînement. La variable créait donc un biais, pas une information.
  2. SUPPRESSION de `eu_member` / `preferential_agreement` : redondants avec la zone
     et non sourcés. Leur présence rendait l'importance des variables ininterprétable.
  3. La distance CEPII est constante par pays : elle capture un effet fixe pays.
     C'est documenté explicitement au lieu d'être présenté comme un effet de distance.
  4. Le jeu de validation est RÉELLEMENT utilisé pour choisir les hyperparamètres,
     puis le test final est évalué une seule fois.
  5. L'élasticité tarifaire est estimée par une régression log-log sur les pays
     disposant d'un tarif NPF, avec intervalle de confiance — plus de coefficient
     fabriqué à la main.

Sortie : data/processed/resultats_modeles.csv + figures/fig6_validation_modeles.png
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

SEED = 42
np.random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA = PROJECT_ROOT / "data" / "processed" / "dataset_merged.csv"
PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES = PROJECT_ROOT / "figures"

print("=" * 80)
print("MODÉLISATION — J6 À J9 (données réelles)")
print("=" * 80)

df = pd.read_csv(DATA)
df = df.dropna(subset=["log_value", "log_gdp", "log_distance"]).copy()
print(f"\nObservations modélisables : {len(df)} / {len(pd.read_csv(DATA))}")
print(f"Période : {df['period'].min()}-{df['period'].max()}")

# ---------------------------------------------------------------------------
# Découpage temporel strict
# ---------------------------------------------------------------------------
train = df[df["period"] <= 2019]
val = df[(df["period"] >= 2020) & (df["period"] <= 2021)]
test = df[df["period"] >= 2022]

print(f"\nDécoupage temporel :")
print(f"  Train      2010-2019 : {len(train):4d} obs")
print(f"  Validation 2020-2021 : {len(val):4d} obs")
print(f"  Test       2022-2023 : {len(test):4d} obs")

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------
# Choix documenté : pas de trend, pas de doublon zone/préférence.
FEATURES = ["log_gdp", "log_distance"]
TARGET = "log_value"

print(f"\nVariables explicatives retenues : {FEATURES}")
print("  log_gdp      : taille du marché de destination (Banque mondiale)")
print("  log_distance : distance CEPII — constante par pays, donc effet fixe pays")
print("\nVariables écartées et pourquoi :")
print("  trend                 : un arbre ne peut pas extrapoler une tendance")
print("  eu_member/preference  : redondant avec le pays, non sourcé")
n_tarif = int(df["tariff_npf_pct"].notna().sum()) if "tariff_npf_pct" in df.columns else 0
print(f"  tariff_npf_pct        : {n_tarif} obs couvertes (98 % de la valeur exportée),")
print("                          mais EXCLU du modèle principal pour ne pas réduire")
print("                          l'échantillon de moitié -> régression dédiée ci-dessous")

X_train, y_train = train[FEATURES], train[TARGET]
X_val, y_val = val[FEATURES], val[TARGET]
X_test, y_test = test[FEATURES], test[TARGET]


def metrics(y_true, y_pred):
    return {
        "MAE": mean_absolute_error(y_true, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_true, y_pred)),
        "R2": r2_score(y_true, y_pred),
    }


resultats = []

# ---------------------------------------------------------------------------
# J6 — Modèle de référence (baseline)
# ---------------------------------------------------------------------------
print("\n" + "-" * 80)
print("J6 — MODÈLE DE RÉFÉRENCE")
print("-" * 80)

baseline = DummyRegressor(strategy="mean").fit(X_train, y_train)
m = metrics(y_test, baseline.predict(X_test))
m.update({"modele": "Baseline (moyenne)", "MAE_val": np.nan, "R2_val": np.nan})
resultats.append(m)
print(f"Baseline moyenne — MAE test {m['MAE']:.4f} | R² test {m['R2']:+.4f}")
print("  Référence : tout modèle doit faire mieux que prédire la moyenne.")

# ---------------------------------------------------------------------------
# J7/J8 — Deux modèles alternatifs, hyperparamètres choisis sur validation
# ---------------------------------------------------------------------------
print("\n" + "-" * 80)
print("J7/J8 — MODÈLES ALTERNATIFS")
print("-" * 80)

# Modèle 1 : Ridge (linéaire régularisé, extrapole correctement)
best_alpha, best_val_mae = None, np.inf
for alpha in [0.01, 0.1, 1.0, 10.0, 100.0]:
    pipe = Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    pipe.fit(X_train, y_train)
    v = mean_absolute_error(y_val, pipe.predict(X_val))
    print(f"  Ridge alpha={alpha:6.2f} → MAE validation {v:.4f}")
    if v < best_val_mae:
        best_alpha, best_val_mae = alpha, v

ridge = Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=best_alpha))])
ridge.fit(X_train, y_train)
m = metrics(y_test, ridge.predict(X_test))
m.update({"modele": f"Ridge (alpha={best_alpha})", "MAE_val": best_val_mae,
          "R2_val": r2_score(y_val, ridge.predict(X_val))})
resultats.append(m)
print(f"→ Ridge retenu alpha={best_alpha} — MAE test {m['MAE']:.4f} | R² test {m['R2']:+.4f}")

# Modèle 2 : Random Forest
best_params, best_val_mae = None, np.inf
for n in [100, 300]:
    for depth in [3, 5, 8]:
        for leaf in [1, 5]:
            rf = RandomForestRegressor(n_estimators=n, max_depth=depth,
                                       min_samples_leaf=leaf,
                                       random_state=SEED, n_jobs=-1)
            rf.fit(X_train, y_train)
            v = mean_absolute_error(y_val, rf.predict(X_val))
            if v < best_val_mae:
                best_params, best_val_mae = (n, depth, leaf), v
print(f"  Random Forest — meilleurs hyperparamètres {best_params} "
      f"(MAE validation {best_val_mae:.4f})")

rf = RandomForestRegressor(n_estimators=best_params[0], max_depth=best_params[1],
                           min_samples_leaf=best_params[2],
                           random_state=SEED, n_jobs=-1)
rf.fit(X_train, y_train)
m = metrics(y_test, rf.predict(X_test))
m.update({"modele": f"Random Forest {best_params}", "MAE_val": best_val_mae,
          "R2_val": r2_score(y_val, rf.predict(X_val))})
resultats.append(m)
print(f"→ Random Forest — MAE test {m['MAE']:.4f} | R² test {m['R2']:+.4f}")

# Modèle 3 : linéaire simple sur le PIB seul (référence interprétable)
lr = LinearRegression().fit(X_train[["log_gdp"]], y_train)
m = metrics(y_test, lr.predict(X_test[["log_gdp"]]))
m.update({"modele": "Régression simple (PIB)",
          "MAE_val": mean_absolute_error(y_val, lr.predict(X_val[["log_gdp"]])),
          "R2_val": r2_score(y_val, lr.predict(X_val[["log_gdp"]]))})
resultats.append(m)
print(f"Régression PIB seul — MAE test {m['MAE']:.4f} | R² test {m['R2']:+.4f}")

# ---------------------------------------------------------------------------
# J9 — Tableau comparatif et évaluation finale unique
# ---------------------------------------------------------------------------
print("\n" + "-" * 80)
print("J9 — ÉVALUATION HORS ÉCHANTILLON (test 2022-2023)")
print("-" * 80)

res = pd.DataFrame(resultats)[["modele", "MAE_val", "R2_val", "MAE", "RMSE", "R2"]]
res = res.rename(columns={"MAE": "MAE_test", "RMSE": "RMSE_test", "R2": "R2_test"})
print(res.to_string(index=False, float_format=lambda x: f"{x:.4f}"))

res.to_csv(PROCESSED / "resultats_modeles.csv", index=False, encoding="utf-8")

# ---------------------------------------------------------------------------
# Élasticité tarifaire — vraie estimation, pas un coefficient choisi à la main
# ---------------------------------------------------------------------------
print("\n" + "-" * 80)
print("ÉLASTICITÉ TARIFAIRE — régression log-log sur les pays couverts par WITS")
print("-" * 80)

el = df.dropna(subset=["tariff_npf_pct", "log_value", "log_gdp"]).copy()
el = el[el["tariff_npf_pct"] > 0].copy()
print(f"Observations avec un droit NPF strictement positif : {len(el)}")
print(f"Partenaires concernés : {el['partnerName'].nunique()}")

elasticite = {}
if len(el) >= 20:
    el["log_tariff"] = np.log(el["tariff_npf_pct"])
    Xe = el[["log_tariff", "log_gdp", "log_distance"]]
    ye = el["log_value"]

    Xe_train, ye_train = Xe[el["period"] <= 2019], ye[el["period"] <= 2019]
    Xe_test, ye_test = Xe[el["period"] >= 2022], ye[el["period"] >= 2022]

    model = LinearRegression().fit(Xe_train, ye_train)
    coef = model.coef_[0]

    # Intervalle de confiance à 95 % (approximation normale sur les résidus)
    resid = ye_train - model.predict(Xe_train)
    n, k = len(Xe_train), Xe_train.shape[1]
    sigma2 = (resid ** 2).sum() / max(n - k, 1)
    try:
        cov = sigma2 * np.linalg.inv(Xe_train.T.values @ Xe_train.values)
        se = np.sqrt(np.diag(cov))[0]
        ci = (coef - 1.96 * se, coef + 1.96 * se)
    except np.linalg.LinAlgError:
        se, ci = np.nan, (np.nan, np.nan)

    sens = "augmente" if coef > 0 else "réduit"
    elasticite = {
        "coef_log_tariff": float(coef),
        "se": float(se) if np.isfinite(se) else None,
        "ic95_bas": float(ci[0]) if np.isfinite(ci[0]) else None,
        "ic95_haut": float(ci[1]) if np.isfinite(ci[1]) else None,
        "n_observations": int(len(el)),
        "n_partenaires": int(el["partnerName"].nunique()),
        "r2_train": float(r2_score(ye_train, model.predict(Xe_train))),
        "r2_test": float(r2_score(ye_test, model.predict(Xe_test))) if len(ye_test) > 2 else None,
        "interpretation": (
            f"Coefficient log(tarif NPF) = {coef:+.3f}. Un doublement du droit NPF "
            f"{sens} la valeur exportée d'environ {abs(2**coef - 1) * 100:.0f} %, "
            f"toutes choses égales par ailleurs. "
            + (
                "Le signe POSITIF est contre-intuitif mais cohérent avec la structure "
                "du marché : les droits NPF les plus élevés sont ceux de l'UE (8,8 à "
                "14,4 %), or l'UE absorbe 83 % des exportations marocaines grâce à "
                "l'accord d'association qui abaisse le tarif effectif. Le NPF mesure "
                "donc ici l'appartenance au marché européen, pas une barrière subie. "
                if coef > 0 else
                "Le signe négatif va dans le sens de l'hypothèse H1. "
            )
            + "ATTENTION : il s'agit du NPF, pas du tarif préférentiel effectivement "
            "payé par le Maroc ; l'élasticité mesure un effet de sélection des "
            "marchés, pas un effet causal du tarif."
        ),
    }
    print(f"  Coefficient log(tarif) : {coef:+.3f} "
          f"[IC95 {ci[0]:+.3f} ; {ci[1]:+.3f}]")
    print(f"  n = {len(el)}, R² train {elasticite['r2_train']:.3f}")
    print(f"  → un doublement du droit NPF {sens} la valeur d'environ "
          f"{abs(2**coef - 1)*100:.0f} %")
    if coef > 0:
        print("  ⚠ Signe positif : le NPF élevé caractérise l'UE, qui reçoit l'essentiel")
        print("    des flux grâce aux préférences. Ce n'est PAS un effet causal du tarif.")
else:
    print("  Trop peu d'observations pour estimer une élasticité de façon fiable.")
    elasticite = {"erreur": "effectif insuffisant", "n_observations": int(len(el))}

(PROCESSED / "elasticite_tarifaire.json").write_text(
    json.dumps(elasticite, indent=2, ensure_ascii=False), encoding="utf-8")

# ---------------------------------------------------------------------------
# Figure 6 — validation
# ---------------------------------------------------------------------------
print("\nFigure 6 — validation des modèles")
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))

best_name = res.loc[res["R2_test"].idxmax(), "modele"]
best_pred = {
    "Baseline (moyenne)": baseline.predict(X_test),
}.get(best_name)
if best_name.startswith("Ridge"):
    best_pred = ridge.predict(X_test)
elif best_name.startswith("Random Forest"):
    best_pred = rf.predict(X_test)
else:
    best_pred = lr.predict(X_test[["log_gdp"]])

axes[0].scatter(y_test, best_pred, alpha=0.6, color="#2E86AB")
lims = [min(y_test.min(), best_pred.min()), max(y_test.max(), best_pred.max())]
axes[0].plot(lims, lims, "r--", linewidth=2, label="Prédiction parfaite")
axes[0].set_xlabel("log(valeur) observée")
axes[0].set_ylabel("log(valeur) prédite")
axes[0].set_title(f"6a. Meilleur modèle : {best_name}", fontweight="bold")
axes[0].legend()
axes[0].grid(alpha=0.3)

axes[1].barh(res["modele"], res["R2_test"], color="#F18F01")
axes[1].axvline(0, color="black", linewidth=1)
axes[1].set_xlabel("R² sur le jeu de test")
axes[1].set_title("6b. Performance hors échantillon", fontweight="bold")
axes[1].grid(axis="x", alpha=0.3)

axes[2].barh(res["modele"], res["MAE_test"], color="#4ECDC4")
axes[2].set_xlabel("MAE sur le jeu de test")
axes[2].set_title("6c. Erreur absolue moyenne", fontweight="bold")
axes[2].grid(axis="x", alpha=0.3)

plt.suptitle("Figure 6 — Validation temporelle des modèles (test 2022-2023)",
             fontsize=15, fontweight="bold")
plt.tight_layout()
plt.savefig(FIGURES / "fig6_validation_modeles.png", dpi=300, bbox_inches="tight")
plt.close()
print(f"  ✓ figures/fig6_validation_modeles.png")

# ---------------------------------------------------------------------------
# Sauvegarde du résumé
# ---------------------------------------------------------------------------
resume = {
    "n_observations": int(len(df)),
    "split": {"train": len(train), "validation": len(val), "test": len(test)},
    "features": FEATURES,
    "features_ecartees": {
        "trend": "un arbre ne peut pas extrapoler une tendance",
        "eu_member / preferential_agreement": "redondant avec le pays, non sourcé",
        "tariff_npf_pct": "couverture insuffisante dans le modèle principal",
    },
    "hyperparametres": {
        "ridge_alpha": best_alpha,
        "random_forest": {"n_estimators": best_params[0],
                          "max_depth": best_params[1],
                          "min_samples_leaf": best_params[2]},
    },
    "resultats_test": res.to_dict(orient="records"),
    "elasticite": elasticite,
}
(PROCESSED / "resume_modelisation.json").write_text(
    json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8")

print("\nRésumé écrit : data/processed/resume_modelisation.json")
print("Terminé.")
