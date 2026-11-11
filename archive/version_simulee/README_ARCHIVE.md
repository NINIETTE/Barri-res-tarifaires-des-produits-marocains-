# Archive — version simulée du projet

**Ne pas utiliser pour le rendu.** Ces fichiers sont conservés uniquement pour la
traçabilité : ils montrent l'état antérieur du projet et permettent de vérifier que les
chiffres ont bien changé.

## Pourquoi cette archive existe

La première version du projet présentait comme « issues d'UN Comtrade » des données
produites par `generate_demo_data.py` : graine 42, dictionnaires de PIB et de distances
codés en dur, tarifs inventés, bruit gaussien ajouté à la main. Le script le montre
lui-même :

```python
final_value = (partner_value * tariff_effect * preferential_effect *
               distance_effect * gdp_effect)
noise = np.random.normal(1, 0.08)
final_value *= noise
```

Aucune de ces valeurs ne provenait d'une source publique. Le rapport affirmait pourtant
« Source principale : UN Comtrade ».

## Chiffres de cette version — à ne PAS citer

| Indicateur | Valeur annoncée (fausse) | Valeur réelle (rapport actuel) |
|---|---|---|
| Observations | 140 (10 pays × 14 ans) | 506 (80 partenaires nommés) |
| $R^2$ test du Random Forest | 0,891 | 0,286 |
| MAE test | 0,282 | 2,738 |
| Élasticité tarifaire | $-0{,}4$ à $-0{,}5$ | $+2{,}22$ $[+0{,}78\,;\,+3{,}65]$ |
| Importance de la distance | 67 % | non mesurée ainsi |
| Effet de l'accord UE | « 9,8 fois » | non reproduit |
| Part de l'UE | 91 % | 83,4 % |

L'élasticité « $-0{,}4$ à $-0{,}5$ » était en réalité calculée ainsi :

```python
elasticite_rf = rf.feature_importances_[0] * (-0.45)  # Approximation
```

C'est-à-dire : une importance de variable multipliée par une constante choisie à la
main. Ce n'est pas une estimation.

## Contenu

| Fichier | Nature |
|---|---|
| `generate_demo_data.py` | Générateur de données simulées |
| `analyse_complete_finale.ipynb` | Notebook utilisant les variables fabriquées (`tariff_rate`, `preferential_agreement`, `eu_member`) |
| `rapport_projet.tex` | Template LaTeX non rempli (24 marqueurs `[À compléter]`) |
| `README_J12_J13.md`, `README_J14_FINAL.md`, `LIVRAISON_FINALE.md` | Documentation de la version simulée |
| `SYNTHESE_FINALE.md`, `SYNTHESE_J1_J2.md`, `INTERPRETATION_ECONOMIQUE.md` | Synthèses reprenant les chiffres faux |
| `PRESENTATION_ORALE.md` | Support de soutenance avec les chiffres faux |
| `GUIDE_J2_J3.md` | Guide de la version simulée |

## Ce qu'il faut utiliser à la place

- **Rapport :** `rapport/rapport.tex` → `rapport/rapport.pdf`
- **Notebook :** `notebooks/analyse_barrieres_tarifaires_maroc.ipynb` (exécuté, 13/13 cellules)
- **Dictionnaire :** `DICTIONNAIRE_VARIABLES.md` (v2.0, séparé par source)
- **Pipeline :** `scripts/extract_real_data.py`, `extract_wits_tariffs.py`,
  `build_dataset.py`, `analyse_exploratoire.py`, `modelisation.py`
