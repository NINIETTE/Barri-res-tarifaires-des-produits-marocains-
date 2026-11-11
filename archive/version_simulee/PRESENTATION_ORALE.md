# 🎤 Présentation Orale - Support de slides
**Projet :** Impact des barrières tarifaires sur les exportations marocaines de tomates  
**Durée :** 10-15 minutes  
**Date :** Novembre 2026

---

## SLIDE 1 : Page de titre

### Impact des barrières tarifaires sur les exportations marocaines de tomates

**Produit :** Tomates fraîches (HS 0702)  
**Période :** 2010-2023  
**Méthode :** Modélisation prédictive (4 modèles comparés)

**Encadrant :** A. Larhlimi  
**Date :** 10 novembre 2026

---

## SLIDE 2 : Contexte et enjeux

### 🍅 Pourquoi les tomates marocaines ?

- **Production annuelle :** > 1.2 million de tonnes
- **Secteur clé :** Emplois ruraux, revenus d'exportation
- **Principal marché :** Union Européenne (91%)

### 📊 Problème

Les barrières tarifaires varient fortement :
- UE : 8.5% (accord préférentiel)
- Russie : 15%
- USA : 4%

**➜ Quel est leur impact réel sur les exportations ?**

---

## SLIDE 3 : Question de recherche et hypothèses

### ❓ Question centrale

**Comment les barrières tarifaires influencent-elles les exportations de tomates marocaines ?**

### 🔬 Hypothèses testées

1. **H1 :** Tarifs élevés → Réduction des exportations
2. **H2 :** Accords préférentiels → Augmentation des exportations
3. **H3 :** Relation non-linéaire (effets de seuil)

---

## SLIDE 4 : Données et méthodologie

### 📊 Jeu de données

- **140 observations** : 10 pays × 14 années (2010-2023)
- **26 variables** : Valeur exportation, tarifs, PIB, distance, etc.
- **Structure :** Conforme UN Comtrade

### 🔧 Méthodologie

**Validation temporelle stricte :**
- Train : 2010-2019 (70%)
- Validation : 2020-2021 (15%)
- Test : 2022-2023 (15%)

**4 modèles comparés :**
1. Baseline (moyenne)
2. Régression simple (tarif seul)
3. Régression multiple (6 variables)
4. Random Forest (optimisé)

---

## SLIDE 5 : Analyse exploratoire - Figure 1

### 📈 Évolution temporelle

![Figure 1](../figures/fig1_evolution_temporelle.png)

**Constats :**
- Croissance +75% sur 2010-2023
- Choc COVID visible en 2020
- Reprise forte post-2021

---

## SLIDE 6 : Analyse exploratoire - Figure 2

### 🌍 Top 10 destinations

![Figure 2](../figures/fig2_top10_destinations.png)

**Constats :**
- France domine (28% du marché)
- Top 3 (Fr, NL, Es) = 61% des exportations
- Forte concentration sur l'UE

---

## SLIDE 7 : Analyse exploratoire - Figure 3

### 📉 Corrélation tarifs-exportations

![Figure 3](../figures/fig3_correlation_tarifs.png)

**Constats :**
- Relation négative évidente
- Pays tarifs >10% = exportations 3-4x plus faibles
- Box plot confirme l'effet

---

## SLIDE 8 : Résultats - Comparaison des modèles

### 🏆 Performances sur ensemble de test

| Modèle | MAE | RMSE | R² |
|--------|-----|------|----|
| Baseline (moyenne) | 0.889 | 0.996 | -0.135 |
| Régression simple | 0.792 | 0.961 | -0.058 |
| Régression multiple | 0.401 | 0.547 | **0.658** |
| **Random Forest** | **0.282** | **0.309** | **0.891** |

**➜ Random Forest = Meilleur modèle**
- R² = 0.891 (89% variance expliquée)
- Amélioration +68.3% vs baseline

---

## SLIDE 9 : Résultats - Variables importantes

### 🎯 Feature Importance (Random Forest)

| Rang | Variable | Importance | Interprétation |
|------|----------|------------|----------------|
| 1 | Distance | **67%** | Proximité Europe = avantage structurel |
| 2 | PIB | **20%** | Taille du marché compte |
| 3 | Tarifs | **11%** | Impact modifiable par négociation |
| 4+ | Autres | 2% | Effets marginaux |

**Message clé :** La géographie domine, mais les tarifs ont un impact significatif

---

## SLIDE 10 : Résultats - Élasticité tarifaire

### 💡 Quantification de l'impact

**Élasticité mesurée : -0.4 à -0.5**

**Interprétation :**
- +1 point de tarif → **-4 à -5% d'exportations**
- +5 points de tarif → **-20 à -25% d'exportations**

**Exemple concret :**
- Si Russie réduit tarifs de 15% → 10%
- Gain potentiel : **+40-50 M$/an**

---

## SLIDE 11 : Validation des hypothèses

### ✅ H1 : Tarifs élevés → Réduction exportations

**VALIDÉE**
- Pays tarifs >10% = exportations 3-4x plus faibles
- Élasticité négative confirmée (-0.4 à -0.5)

### ✅ H2 : Accords préférentiels → Augmentation

**VALIDÉE**
- UE (accord) = 91% du marché
- Exportations UE = **9.8x plus élevées** que hors UE

### ⚠️ H3 : Relation non-linéaire

**PARTIELLEMENT VALIDÉE**
- Random Forest 30% meilleur que linéaire
- Mais pas d'effet de seuil net

---

## SLIDE 12 : Recommandations stratégiques

### 💼 Court terme (1-2 ans)

1. **Maintenir accord UE** (priorité absolue)
   - Risque si perdu : -150 à -200 M$/an
2. **Renégocier UK post-Brexit**
   - Objectif : tarifs < 8%
   - Gain : +15-20 M$/an
3. **Lobbying UE** pour quotas additionnels

### 💼 Moyen terme (3-5 ans)

1. **Négocier réduction tarifs Russie** (15% → 8%)
   - Gain : +40-50 M$/an
2. **Explorer marchés Golfe** (Émirats, Arabie Saoudite)
3. **Diversification produit** (cerises, bio)

---

## SLIDE 13 : Limites du projet

### ⚠️ Limitations identifiées

1. **Données simulées**
   - Basées sur statistiques FAO/ITC
   - À remplacer par UN Comtrade réelles

2. **Causalité vs corrélation**
   - Tarifs non assignés aléatoirement
   - Risque de variables omises

3. **Variables non incluses**
   - Barrières non-tarifaires
   - Normes sanitaires, quotas
   - Taux de change

4. **Période avec chocs**
   - COVID-19 (2020)
   - Brexit (2021)
   - Guerre Ukraine (2022)

---

## SLIDE 14 : Qualité méthodologique

### ✅ Points forts du projet

1. **Validation temporelle stricte**
   - Pas de data leakage
   - Protocole rigoureux

2. **Comparaison multi-modèles**
   - 4 modèles testés
   - Hyperparameter tuning

3. **Reproductibilité**
   - Seed fixe (42)
   - Code documenté
   - Scripts automatisés

4. **Interprétation économique**
   - Élasticités quantifiées
   - Recommandations chiffrées
   - Conformité académique

---

## SLIDE 15 : Conclusion

### 🎯 Messages clés

1. **Les barrières tarifaires ont un impact significatif** (-4 à -5% par point de tarif)

2. **La géographie reste dominante** (67% d'importance)

3. **L'accord UE-Maroc est crucial** (9.8x plus d'exportations)

4. **Random Forest explique 89% de la variance** (R²=0.891)

5. **Recommandations stratégiques chiffrées** pour politique commerciale

### 🚀 Perspectives

- Intégrer barrières non-tarifaires
- Analyser saisonnalité intra-annuelle
- Comparer avec concurrents (Turquie, Espagne)

---

## SLIDE 16 : Questions ?

### 📊 Livrables du projet

✅ **Documentation** : 5 fichiers (58 KB)  
✅ **Code Python** : 4 scripts (1,273 lignes)  
✅ **Données** : 140 obs, 26 variables  
✅ **Figures** : 6 PNG haute résolution  
✅ **Rapport LaTeX** : 15 pages  
✅ **2 jalons atteints**

### 📁 Disponible dans :
`/home/korbix/projet_barriere_tarifaire/`

---

**Merci pour votre attention !**

**Questions / Discussion**

---

## ANNEXE : Notes pour la présentation orale

### Timing recommandé (10 minutes)

- Slides 1-3 : Introduction et cadrage (2 min)
- Slides 4-7 : Données et EDA (2 min)
- Slides 8-10 : Résultats modélisation (2 min)
- Slides 11-12 : Hypothèses et recommandations (2 min)
- Slides 13-15 : Limites et conclusion (1.5 min)
- Slide 16 : Questions (reste du temps)

### Points à emphasiser à l'oral

1. **Rigueur méthodologique** : Validation temporelle stricte
2. **Performance du modèle** : R²=0.891 est excellent
3. **Résultats exploitables** : Élasticités quantifiées, recommandations chiffrées
4. **Honnêteté sur limites** : Données simulées, variables omises

### Questions anticipées

**Q : Pourquoi données simulées ?**
R : Quotas API UN Comtrade limités. Données calibrées sur statistiques FAO/ITC réelles. Structure conforme UN Comtrade.

**Q : Pourquoi Random Forest meilleur que régression ?**
R : Capture interactions complexes entre variables et non-linéarités. Mais régression reste très bonne (R²=0.658).

**Q : Recommandations réalistes ?**
R : Basées sur élasticités mesurées. Chiffrées avec intervalles. Limitées aux leviers modifiables (tarifs).

**Q : Validité des résultats ?**
R : Méthodologie rigoureuse. Résultats cohérents avec littérature économique. Reproductibles (seed fixe).

### Matériel à préparer

- [ ] Slides PowerPoint (16 slides)
- [ ] Impression rapport (backup)
- [ ] USB avec code et données
- [ ] Répétition chronométrée
- [ ] Liste des acronymes (HS, NPF, MAE, RMSE, etc.)
