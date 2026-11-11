# Dictionnaire des variables

**Projet :** Barrières tarifaires sur les exportations marocaines de tomates (HS 0702)
**Date :** 11 novembre 2026
**Version :** 2.0 — données réelles

> **Changement majeur par rapport à la v1.0 :** la version précédente décrivait un jeu de
> données simulé (`archive/version_simulee/generate_demo_data.py`) et attribuait à
> « OMC / Accords » des variables tarifaires qui n'existaient pas. Les 506 observations
> actuelles proviennent d'APIs publiques, chacune tracée jusqu'à son endpoint dans
> `data/raw/metadata_extraction.json`, `data/raw/metadata_wits.json` et
> `data/processed/metadata_dataset.json`.

---

## 1. Source 1 — UN Comtrade (exportations)

**Endpoint :** `https://comtradeapi.un.org/public/v1/preview/C/A/HS`
**Paramètres :** `reporterCode=504` (Maroc), `cmdCode=0702`, `flowCode=X`, `period=2010-2023`
**Date d'extraction :** 2026-11-11
**Licence :** données publiques ONU — citation obligatoire
**Volume :** 506 lignes, 83 partenaires déclarés

| Variable | Type | Unité | Description | Rôle |
|----------|------|-------|-------------|------|
| `period` | int | année | Année du flux (2010-2023) | Index temporel |
| `reporterCode` | int | code | 504 = Maroc | Identification |
| `reporterDesc` | str | - | « Morocco » | Label |
| `partnerCode` | int | code | Code du pays importateur (numérique) | Identification |
| `partnerName` | str | - | Nom du pays importateur, résolu via le référentiel Comtrade `Reporters.json` | Label |
| `iso3` | str | code | Code ISO3 dérivé de `partnerCode` | Clé de fusion |
| `flowCode` | str | code | `X` = exportation | Classification |
| `flowDesc` | str | - | « Export » | Label |
| `cmdCode` | str | HS | `0702` — tomates fraîches ou réfrigérées | Identification |
| `cmdDesc` | str | - | Libellé du produit | Label |
| `primaryValue` | float | USD | **Valeur exportée** — variable cible | **Cible** |
| `netWgt` | float | kg | Poids net exporté | Cible alternative |
| `qty` | float | - | Quantité déclarée | Info |
| `qtyUnitAbbr` | str | - | Unité de `qty` — **100 % manquante** dans l'API preview | Non utilisée |

**Points de vigilance :**

- L'endpoint *preview* plafonne à 500 lignes par requête et renvoie `partnerDesc: null`.
  Les noms de pays sont donc récupérés séparément depuis
  `https://comtradeapi.un.org/files/v1/app/reference/Reporters.json`.
- 3 codes partenaires (837, 838, 899) restent sans nom et sans ISO3 : 8 observations.
  Ils sont conservés mais exclus des fusions PIB / distance. Ce manque est déclaré, pas imputé.
- `qtyUnitAbbr` est vide à 100 % : la colonne est conservée pour la traçabilité mais
  n'entre dans aucun calcul.

---

## 2. Source 2 — Banque mondiale (PIB)

**Endpoint :** `https://api.worldbank.org/v2/country/{iso3}/indicator/NY.GDP.MKTP.CD?format=json&date=2010:2023`
**Indicateur :** `NY.GDP.MKTP.CD` — PIB courant, USD
**Licence :** CC BY 4.0
**Volume :** 896 valeurs, 64 pays

| Variable | Type | Unité | Description | Rôle |
|----------|------|-------|-------------|------|
| `gdp_partner_usd` | float | USD | PIB courant du pays importateur | Variable de contrôle |
| `log_gdp` | float | - | `ln(gdp_partner_usd)` | Linéarisation |

**Couverture :** 434 / 506 observations (85,8 %). Les 72 manquantes correspondent à des
partenaires hors référentiel Banque mondiale ou sans déclaration pour l'année.

---

## 3. Source 3 — WITS / UNCTAD TRAINS (tarifs)

**Endpoint :** `https://wits.worldbank.org/API/V1/SDMX/V21/datasource/TRN/reporter/{rep}/partner/000/product/070200/year/{year}/datatype/reported`
**Date d'extraction :** 2026-11-11
**Licence :** CC BY 4.0 (Banque mondiale)

| Variable | Type | Unité | Description | Rôle |
|----------|------|-------|-------------|------|
| `tariff_npf_pct` | float | % | Droit **NPF** (Most Favoured Nation), moyenne simple sur les lignes HS6 | Variable explicative |
| `tariff_source_type` | str | - | `MFN` | Traçabilité |
| `tariff_measure` | str | - | `SimpleAverage` | Traçabilité |
| `tariff_n_lines` | int | - | Nombre de lignes tarifaires agrégées | Traçabilité |
| `wits_reporter` | int | code | Déclarant WITS utilisé (918 = UE agrégée) | Clé de fusion |

> ### ⚠️ Limite fondamentale — à ne jamais masquer dans le rapport
>
> `tariff_npf_pct` est le **droit NPF**, c'est-à-dire le tarif appliqué aux pays **sans**
> accord préférentiel. Le Maroc, lui, bénéficie de l'accord d'association UE-Maroc (2000) :
> ses tomates entrent en franchise ou à taux réduit, **bien en dessous du NPF**.
>
> L'API WITS ne fournit pas le taux préférentiel Maroc (`partner/504` renvoie 404 pour la
> plupart des déclarants). La variable mesure donc **le tarif que subirait le Maroc s'il
> n'avait pas d'accord**, et non le tarif qu'il paie réellement.
>
> Conséquence : toute « élasticité tarifaire » estimée sur cette variable mesure un effet
> de sélection des marchés, pas un effet causal du tarif. C'est écrit dans
> `metadata_wits.json` et repris tel quel dans le rapport.

**Couverture :** 10 déclarants (UE agrégée, Royaume-Uni, Russie, Suisse, Arabie saoudite,
Émirats, États-Unis, Japon, Chine, Inde), soit les partenaires couvrant 94 % de la valeur
exportée. Les autres pays ne sont pas couverts — aucune valeur n'est inventée.

---

## 4. Source 4 — CEPII (distances)

**Fichier :** `https://www.cepii.fr/distance/dist_cepii.zip` → `dist_cepii.xls`
**Licence :** utilisation libre, citation CEPII

| Variable | Type | Unité | Description | Rôle |
|----------|------|-------|-------------|------|
| `distance_km_cepii` | float | km | Distance pondérée entre Maroc et le partenaire | Variable de contrôle |
| `contigu` | int | 0/1 | Frontière commune avec le Maroc | Contrôle |
| `langue_officielle_commune` | int | 0/1 | Langue officielle partagée | Contrôle |
| `log_distance` | float | - | `ln(distance_km_cepii)` | Linéarisation |

**Couverture :** 491 / 506 (97,0 %). **La distance est constante par pays** : elle ne varie
pas d'une année à l'autre. Dans un modèle de panel, elle agit donc comme un **effet fixe
pays**, pas comme un effet de distance au sens strict.

---

## 5. Variables calculées (transformations, aucune donnée nouvelle)

| Variable | Formule | Rôle |
|----------|---------|------|
| `log_value` | `ln(primaryValue)` si > 0, sinon NaN | Cible transformée |
| `log_weight` | `ln(netWgt)` si > 0, sinon NaN | Cible alternative |
| `prix_unitaire_usd_kg` | `primaryValue / netWgt` si `netWgt > 0` | Indicateur de valeur unitaire |
| `annee_precedente` | `period` décalé de 1 dans chaque partenaire | Contrôle de continuité |
| `intervalle_annees` | `period − annee_precedente` | Détection des trous |
| `lag_value` | `primaryValue` décalé de 1 dans chaque partenaire | Autorégression |
| `growth_rate_pct` | `(V_t − V_{t−1}) / V_{t−1} × 100`, **uniquement si `intervalle_annees == 1`** | Dynamique |
| `trend` | `period − 2010` | **Créée mais écartée des modèles** (voir §7) |

`growth_rate_pct` est calculé seulement sur des années consécutives : sans cette précaution,
un pays observé en 2010 puis en 2014 produisait une « croissance » de +5543 % qui n'a
aucun sens économique.

---

## 6. Statistiques descriptives réelles

### Variables continues (506 observations)

| Variable | Min | Médiane | Moyenne | Max | Manquants |
|----------|-----|---------|---------|-----|-----------|
| `primaryValue` (USD) | 2 | 149 836 | 17,7 M | 682,2 M | 0 |
| `netWgt` (kg) | 2 | 182 035 | 15,0 M | 375,3 M | 0 |
| `gdp_partner_usd` (USD) | 1,6 Md | 256 Md | 1 072 Md | 27 811 Md | 72 (14,2 %) |
| `distance_km_cepii` (km) | 271 | 2 833 | 3 371 | 11 829 | 15 (3,0 %) |
| `tariff_npf_pct` (%) | — | — | — | — | voir §3 |

### Concentration géographique

| Rang | Partenaire | Cumul 2010-2023 | Part |
|------|-----------|-----------------|------|
| 1 | France | 5 937 M$ | 66,4 % |
| 2 | Royaume-Uni | 923 M$ | 10,3 % |
| 3 | Espagne | 568 M$ | 6,4 % |
| 4 | Pays-Bas | 535 M$ | 6,0 % |
| 5 | Russie | 461 M$ | 5,2 % |

Top 5 = **94,2 %** des exportations. Total 2010-2023 : **8 947 M$**.

### Évolution annuelle (M$)

| 2010 | 2013 | 2016 | 2019 | 2020 | 2022 | 2023 |
|------|------|------|------|------|------|------|
| 300 | 429 | 512 | 784 | 787 | 1 025 | 1 140 |

---

## 7. Variables écartées et justification

| Variable | Raison de l'exclusion |
|----------|----------------------|
| `trend` | Un modèle à arbres ne sait pas extrapoler une tendance : avec un découpage temporel, il plafonne à la dernière valeur vue en entraînement. La variable introduisait un biais, pas une information. |
| `eu_member` / `preferential_agreement` | Redondants avec le pays (effet fixe) et **non sourcés** dans la version précédente. Supprimés plutôt que fabriqués. |
| `high_tariff` | Dérivée d'un `tariff_rate` qui n'existait pas réellement. |
| `lag_weight` | Jamais produit par le pipeline réel. |
| `region` | Remplacé par `zone` (UE / hors UE), calculé à partir d'`iso3`. |

---

## 8. Utilisation dans les modèles

**Cible :** `log_value`

**Variables explicatives du modèle principal :** `log_gdp`, `log_distance`

**Traitement séparé :** `tariff_npf_pct` n'est pas dans le modèle principal car sa
couverture est partielle (10 déclarants). Il fait l'objet d'une **régression log-log
dédiée** sur les observations couvertes, avec intervalle de confiance à 95 %.

**Validation temporelle :**

| Jeu | Période | Rôle |
|-----|---------|------|
| Train | 2010-2019 | Apprentissage + choix des hyperparamètres par validation croisée temporelle |
| Validation | 2020-2021 | Sélection des hyperparamètres (Ridge α, Random Forest) |
| Test | 2022-2023 | Évaluation finale, une seule fois |

Aucun mélange temporel : le modèle ne voit jamais le futur.

---

## 9. Limites méthodologiques

1. **Le tarif NPF n'est pas le tarif subi** (§3). C'est la limite la plus importante.
2. **Causalité :** les tarifs ne sont pas assignés aléatoirement. Les estimations sont des
   associations conditionnelles, pas des effets causaux.
3. **Barrières non tarifaires absentes :** quotas, normes sanitaires, certificats
   phytosanitaires ne sont pas mesurés. Pour les produits frais, leur poids peut dépasser
   celui des droits de douane.
4. **Distance constante par pays** : elle ne peut pas être distinguée d'un effet fixe pays.
5. **3 codes partenaires non résolus** (837, 838, 899) : 8 observations sans nom.

---

## 10. Reproductibilité

```bash
cd ~/projet_barriere_tarifaire
source venv/bin/activate
python scripts/extract_real_data.py      # Comtrade + Banque mondiale
python scripts/extract_wits_tariffs.py   # WITS (lent, ~15 min, cache par requête)
python scripts/build_dataset.py          # fusion + variables calculées
python scripts/analyse_exploratoire.py   # EDA, 5 figures
python scripts/modelisation.py           # modèles + élasticité
```

Chaque extraction écrit ses métadonnées (URL, date, paramètres, licence) dans
`data/raw/metadata_*.json`. Aucune valeur n'est codée en dur dans les scripts d'analyse.

---

**Nombre de variables dans `dataset_merged.csv` :** 28
**Variables utilisées dans les modèles :** 2 (+ 1 en régression dédiée)
