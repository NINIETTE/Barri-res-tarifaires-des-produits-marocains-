# 🍅 Barrières tarifaires et exportations marocaines de tomates

## 📖 Description du projet

Analyse quantitative de l'impact des droits de douane sur les exportations de tomates
fraîches du Maroc (HS 0702) vers ses principaux partenaires commerciaux.

**Période d'étude :** 2010-2023
**Type :** Projet académique Data Science (14 jours) — Projet 35 du catalogue
**Niveau :** Master Commerce International
**Établissement :** ENCG Settat

---

## 🎯 Objectifs

1. **Décrire et classer** les marchés selon les droits de douane appliqués au produit
   HS 0702 (tâche demandée par le catalogue : « analyse descriptive + classement »)
2. **Comparer plusieurs approches de modélisation** avec validation temporelle stricte
3. **Fournir des recommandations** pour les négociations commerciales

---

## 📊 Sources de données — toutes réelles, toutes tracées

| Source | Ce qu'elle fournit | Endpoint | Licence |
|--------|-------------------|----------|---------|
| **UN Comtrade** | Exportations Maroc → 83 partenaires, HS 0702, 2010-2023 | `comtradeapi.un.org/public/v1/preview/C/A/HS` | Données publiques ONU |
| **Banque mondiale (WDI)** | PIB courant des partenaires | `api.worldbank.org/v2/.../NY.GDP.MKTP.CD` | CC BY 4.0 |
| **WITS / UNCTAD TRAINS** | Droits **NPF** HS 070200, 10 déclarants | `wits.worldbank.org/API/V1/SDMX/V21/...` | CC BY 4.0 |
| **CEPII** | Distances bilatérales depuis le Maroc | `cepii.fr/distance/dist_cepii.zip` | Citation CEPII |

> **Aucune donnée simulée.** La version précédente du projet utilisait un générateur
> de données (`generate_demo_data.py`, seed 42, PIB et distances codés en dur, tarifs
> inventés). Ce script n'est plus appelé par aucun pipeline : il est déplacé dans
> `archive/version_simulee/`, avec un `README_ARCHIVE.md` qui documente l'écart entre
> les chiffres fabriqués et les chiffres réels.

### ⚠️ Limite majeure à connaître avant de lire les résultats

Les droits extraits de WITS sont des **droits NPF** (Most Favoured Nation), c'est-à-dire
ce que paierait le Maroc **s'il n'avait pas d'accord préférentiel**. Sous l'accord
d'association UE-Maroc, les tomates marocaines entrent en franchise ou à taux réduit.
L'API ne fournit pas le taux préférentiel Maroc (`partner/504` → 404).

**Conséquence :** l'« élasticité tarifaire » estimée mesure un effet de sélection des
marchés, pas un effet causal du tarif payé. C'est documenté dans `metadata_wits.json` et
dans le rapport.

---

## 🗂️ Structure du projet

```
projet_barriere_tarifaire/
│
├── data/
│   ├── raw/
│   │   ├── api_cache/                        # Réponses Comtrade brutes (rejouable hors ligne)
│   │   ├── wits_cache/                       # Réponses WITS brutes
│   │   ├── comtrade_maroc_tomates_2010_2023.csv
│   │   ├── worldbank_gdp_partners.csv
│   │   ├── wits_tarifs_npf_2010_2023.csv
│   │   ├── cepii_distances_mar.csv
│   │   └── metadata_*.json                   # URL, date, paramètres, licence de chaque source
│   ├── processed/
│   │   ├── dataset_merged.csv                # Dataset final (506 obs × 32 var)
│   │   ├── resultats_modeles.csv
│   │   ├── resume_modelisation.json
│   │   ├── elasticite_tarifaire.json
│   │   └── interpretations_eda.json
│   └── logs/
│
├── notebooks/
│   └── analyse_barrieres_tarifaires_maroc.ipynb   # exécuté, 13/13 cellules
│
├── scripts/
│   ├── extract_real_data.py      # Comtrade + Banque mondiale (avec cache + backoff)
│   ├── extract_wits_tariffs.py   # WITS / UNCTAD TRAINS (parallèle, cache par requête)
│   ├── build_dataset.py          # Fusion des 4 sources + variables calculées
│   ├── analyse_exploratoire.py   # Contrôle qualité + 5 figures commentées (JALON 1)
│   ├── modelisation.py           # Modèles + élasticité (J6-J9)
│   ├── generate_notebook.py      # Génère le notebook exécutable
│   └── test_reproductibilite.py  # Vérifie tout le pipeline
│
├── figures/                      # fig1 à fig6
├── rapport/
│   └── rapport.tex               # Rapport LaTeX (15 p.)
├── soutenance/
│   └── soutenance.tex            # Support beamer (18 vues)
├── archive/version_simulee/      # Ancienne version — NE PAS UTILISER
├── DICTIONNAIRE_VARIABLES.md     # Dictionnaire détaillé par source
└── README.md
```

---

## 🚀 Installation

```bash
cd ~/projet_barriere_tarifaire
python3 -m venv venv
venv/bin/pip install -r requirements.txt
```

> Sur les distributions récentes, `pip install` système est bloqué par PEP 668.
> Toujours passer par `venv/bin/pip` et exécuter les scripts avec `venv/bin/python`.

---

## 📥 Reproduire le pipeline complet

```bash
cd ~/projet_barriere_tarifaire

# 1. Exportations (Comtrade) + PIB (Banque mondiale) — ~2 min avec cache
venv/bin/python scripts/extract_real_data.py

# 2. Droits NPF (WITS) — ~15 min, 140 requêtes parallèles, cache par requête
venv/bin/python scripts/extract_wits_tariffs.py

# 3. Fusion + variables calculées
venv/bin/python scripts/build_dataset.py

# 4. EDA — contrôle qualité + 5 figures commentées
venv/bin/python scripts/analyse_exploratoire.py

# 5. Modélisation + élasticité
venv/bin/python scripts/modelisation.py
```

Chaque extraction écrit un fichier `metadata_*.json` contenant l'URL appelée, la date,
les paramètres et la licence. Les réponses HTTP sont mises en cache : relancer un script
ne re-interroge pas les serveurs.

---

## 📈 Résultats

| Indicateur | Valeur |
|---|---|
| Exportations 2010 → 2023 | 299,7 → 1 140,3 M USD (+280 %, 10,8 %/an) |
| Premier marché | France — 66,4 % du total |
| Top 5 | 94,2 % du total |
| Part de l'UE | 83,4 % |
| HHI | 0,652 (2010) → 0,395 (2023) |
| Meilleur modèle (test) | Random Forest, R² = 0,286, MAE = 2,738 |
| Baseline (moyenne) | R² = −0,002 |
| Élasticité au droit NPF | +2,22 [IC95 +0,78 ; +3,65], n = 174 |

**Performances détaillées** (cible : `log_value`)

| Modèle | MAE val | R² val | MAE test | RMSE test | R² test |
|---|---:|---:|---:|---:|---:|
| Baseline (moyenne) | — | — | 3,519 | 4,318 | −0,002 |
| Régression simple (PIB) | 2,538 | 0,228 | 3,152 | 4,309 | 0,002 |
| Ridge (α = 1) | 2,337 | 0,382 | 2,887 | 3,825 | 0,213 |
| **Random Forest (300, 8, 1)** | **1,878** | **0,545** | **2,738** | **3,644** | **0,286** |

Un R² de 0,286 laisse 71 % de la variance inexpliquée. Deux variables ne suffisent pas à
décrire la répartition des flux : le modèle est présenté comme un banc d'essai
méthodologique, pas comme un outil prédictif.

---

## 🧪 Modèles comparés

| Modèle | Rôle |
|--------|------|
| **Baseline (moyenne)** | Référence minimale : tout modèle doit faire mieux que prédire la moyenne |
| **Régression simple (PIB)** | Référence interprétable sur une seule variable |
| **Ridge** | Linéaire régularisé, α choisi sur validation |
| **Random Forest** | Non paramétrique, hyperparamètres choisis sur validation |

**Variables :** `log_gdp`, `log_distance`.
**Cible :** `log_value`.

**Écartées et pourquoi :**
- `trend` — un arbre ne peut pas extrapoler une tendance ; avec un split temporel il
  plafonne à la dernière valeur vue en entraînement.
- `eu_member` / `preferential_agreement` — redondants avec l'effet fixe pays, et non
  sourcés dans la version simulée.
- `tariff_npf_pct` — couverture partielle (10 déclarants) ; traité par une régression
  log-log dédiée avec intervalle de confiance.

---

## 📈 Métriques

- **MAE** et **RMSE** sur `log_value`
- **R²** hors échantillon
- **Élasticité tarifaire** : coefficient log-log + IC 95 %

**Découpage temporel strict :** train 2010-2019, validation 2020-2021, test 2022-2023.
Le test n'est évalué qu'une fois.

---

## 📅 Avancement

| Jour | Tâche | Statut |
|------|-------|--------|
| J1-J2 | Cadrage + identification produit (Projet 35) | ✅ |
| J2-J3 | Extraction données réelles | ✅ |
| J3 | Dictionnaire variables (v2.0, par source) | ✅ |
| J4 | Nettoyage + contrôle qualité | ✅ |
| J5 | EDA + 5 figures ⭐ JALON 1 | ✅ |
| J6 | Baseline | ✅ |
| J7-J8 | Modèles alternatifs | ✅ |
| J9 | Validation temporelle | ✅ |
| J10 | Interprétation ⭐ JALON 2 | ✅ |
| J11 | Sensibilité | ✅ |
| J12-J13 | Rapport LaTeX | ✅ |
| J14 | Finalisation | ✅ |

---

## 📚 Références

1. UN Comtrade (2026). *UN Comtrade Database*. https://comtradeapi.un.org/
2. Banque mondiale (2026). *World Development Indicators*. https://data.worldbank.org/
3. Banque mondiale / UNCTAD (2026). *WITS — World Integrated Trade Solution*. https://wits.worldbank.org/
4. CEPII (2026). *GeoDist — dist_cepii*. https://www.cepii.fr/CEPII/en/bdd_modele/bdd.asp
5. Baier, S. & Bergstrand, J. (2007). "Do free trade agreements actually increase members' international trade?". *Journal of International Economics*, 71(1).
6. Head, K. & Mayer, T. (2014). "Gravity Equations: Workhorse, Toolkit, and Cookbook". *Handbook of International Economics*, Vol. 4.

---

## ⚠️ Avertissements

- **Tarif NPF ≠ tarif subi** : voir la section « Limite majeure » ci-dessus.
- **Quotas API** : Comtrade preview plafonne à 500 lignes par requête et limite le débit
  (HTTP 429). Les scripts gèrent le backoff et mettent en cache.
- **Données manquantes** : certains pays ne déclarent pas certaines années. Aucune
  imputation n'est faite ; les valeurs restent manquantes et sont signalées.
- **Causalité** : les modèles mesurent des associations conditionnelles, pas des liens
  causaux.

---

## 👥 Auteurs

- **Étudiante 1 :** Hiba Yacoubi
- **Étudiante 2 :** Meriem Ninia

**Encadrant :** A. Larhlimi
**Établissement :** École Nationale de Commerce et de Gestion de Settat (ENCG Settat) — Master Commerce International
**Année universitaire :** 2026-2027

---

## 📝 Licence

Le code (`.py`, `.ipynb`, `.tex`) est publié sous **licence MIT**. Le texte du rapport,
les figures et le support de soutenance sont sous **CC BY 4.0**. Les données brutes
restent soumises aux licences de leurs producteurs (voir le tableau des sources et
`LICENSE`).

---

**Dernière mise à jour :** 11 novembre 2026
**Version :** 2.0 — données réelles
