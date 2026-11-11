# Projet Data Science : Barrières tarifaires sur les exportations marocaines

## 📋 Informations générales
- **Durée :** 14 jours
- **Type :** Projet en binôme
- **Plateforme :** Google Colab / Jupyter Notebook
- **Date de début :** 10 novembre 2026

---

## 🎯 Problématique de recherche

### Produit choisi : Tomates fraîches du Maroc
**Code HS :** 0702 (Tomates fraîches ou réfrigérées)

### Question de recherche principale
**Comment les barrières tarifaires appliquées par les principaux partenaires commerciaux (UE, Russie, USA) influencent-elles le volume et la valeur des exportations de tomates marocaines ?**

### Hypothèses
1. **H1 :** Les droits de douane élevés réduisent significativement le volume d'exportation vers les marchés protégés
2. **H2 :** Les accords préférentiels (ex: accord Maroc-UE) augmentent les exportations vers ces marchés
3. **H3 :** La saisonnalité des exportations est influencée par les quotas tarifaires temporaires

### Justification du choix
- **Importance économique :** Le Maroc est l'un des plus grands exportateurs de tomates en Afrique
- **Diversité des marchés :** Exportations vers UE (majoritaire), Russie, pays arabes
- **Régime tarifaire complexe :** Quotas, accords préférentiels, contingents tarifaires
- **Données disponibles :** UN Comtrade, WTO, Eurostat

---

## 📊 Sources de données identifiées

### Source principale : UN Comtrade API
- **URL :** https://comtradeapi.un.org/
- **Documentation :** https://uncomtrade.org/docs/
- **Couverture :** 2010-2023 (données annuelles et mensuelles)
- **Reporter :** Maroc (code 504)
- **Commodity :** HS 0702 (Tomates)
- **Flow :** Exportations (code X)
- **Quotas :** 100 000 requêtes/heure (version publique)

### Sources complémentaires — ce qui a réellement été utilisé

1. **WITS / UNCTAD TRAINS** : https://wits.worldbank.org/
   - Droits **NPF** HS 070200, moyenne simple
   - 10 déclarants couvrant 98,2 % de la valeur exportée
   - ⚠️ Ne fournit **pas** le taux préférentiel Maroc (`partner/504` → 404)

2. **Banque mondiale — WDI**
   - PIB courant `NY.GDP.MKTP.CD` des partenaires
   - 85,8 % des observations couvertes

3. **CEPII — dist_cepii**
   - Distances bilatérales depuis le Maroc, contiguïté, langue
   - 97,0 % des observations couvertes

> **Note.** La source « WTO Tariff Data » initialement prévue n'a pas d'API publique
> sans clé. WITS, qui reprend les mêmes données TRAINS, a été utilisée à la place. La
> question du taux préférentiel reste ouverte et constitue la limite principale du
> projet (voir rapport, §2.5).

---

## 📈 Variables cibles et explicatives

### Variable cible
- **Valeur des exportations** (USD) par destination et année
- Ou **Volume d'exportations** (tonnes)

### Variables explicatives potentielles
1. **Barrières tarifaires**
   - Taux de droit de douane effectif (%)
   - Existence d'accord préférentiel (binaire)
   - Quotas tarifaires

2. **Facteurs économiques**
   - PIB du pays importateur
   - Distance géographique
   - Taux de change MAD/devise locale

3. **Facteurs temporels**
   - Année
   - Saisonnalité (si données mensuelles)
   - Tendance

---

## 🎯 Objectifs mesurables du projet

### Objectif 1 : Quantifier l'impact tarifaire
Mesurer l'élasticité des exportations marocaines de tomates aux droits de douane appliqués

### Objectif 2 : Comparer les modèles prédictifs
Comparer au moins 3 approches :
- Baseline : moyenne mobile ou régression linéaire simple
- Modèle 1 : Régression linéaire multiple avec variables tarifaires
- Modèle 2 : Random Forest ou Gradient Boosting

### Objectif 3 : Fournir des recommandations
Identifier les marchés prioritaires et les stratégies de négociation tarifaire

---

## 📅 Calendrier détaillé

| Jour | Tâche | Livrable |
|------|-------|----------|
| J1-J2 | Cadrage + identification produit | ✅ Ce document |
| J2-J3 | Accès données + extraction | Script Python + CSV bruts |
| J3 | Dictionnaire variables | Tableau documenté |
| J4 | Nettoyage données | Journal transformations |
| J5 | EDA + 5 figures | **JALON 1** : Figures commentées |
| J6 | Baseline | Métriques de référence |
| J7 | Modèle alternatif 1 | Code + résultats |
| J8 | Modèle alternatif 2 | Hyperparamètres optimisés |
| J9 | Validation hors échantillon | Comparaison rigoureuse |
| J10 | Interprétation économique | **JALON 2** : Rapport intermédiaire |
| J11 | Sensibilité et limites | Analyse de robustesse |
| J12-J13 | Rédaction LaTeX | PDF provisoire |
| J14 | Finalisation | Notebook + présentation |

---

## ⚠️ Risques et limitations identifiés

### Risques techniques
- **Quota API limité** : Nécessité de planifier les requêtes
- **Données manquantes** : Certains pays ne reportent pas systématiquement
- **Nomenclature HS** : Changements de classification entre révisions

### Limitations méthodologiques
- **Causalité vs corrélation** : Les tarifs ne sont pas assignés aléatoirement
- **Variables omises** : Barrières non-tarifaires difficiles à quantifier
- **Validation temporelle obligatoire** : Pas de mélange passé/futur

---

## 📚 Références initiales

1. UN Comtrade. (2026). *UN Comtrade Database*. https://comtradeapi.un.org/
2. WTO. (2026). *Tariff Analysis Online*. https://tao.wto.org/
3. Baier, S. & Bergstrand, J. (2007). "Do free trade agreements actually increase members' international trade?". *Journal of International Economics*, 71(1).
4. Head, K. & Mayer, T. (2014). "Gravity Equations: Workhorse, Toolkit, and Cookbook". *Handbook of International Economics*, Vol. 4.

---

## 👥 Organisation du binôme

### Étudiante 1 : Hiba Yacoubi
- Responsable : Extraction données, nettoyage, modèle baseline

### Étudiante 2 : Meriem Ninia
- Responsable : EDA, modèles alternatifs, rédaction rapport

### Tâches partagées
- Définition problématique
- Interprétation économique
- Présentation orale

---

## ✅ Étapes réalisées

1. ✅ Valider le choix du produit (tomates HS 0702) — Projet 35 du catalogue
2. ✅ Extraire les données UN Comtrade (506 obs., 2010-2023, 80 partenaires)
3. ✅ Récupérer les PIB (Banque mondiale, 434 obs.)
4. ✅ Récupérer les droits NPF (WITS, 246 obs., 98,2 % de la valeur)
5. ✅ Récupérer les distances (CEPII, 491 obs.)
6. ✅ Construire le dataset fusionné (`data/processed/dataset_merged.csv`)
7. ✅ EDA et 5 figures commentées (Jalon 1)
8. ✅ Modélisation et validation temporelle (Jalon 2)
9. ✅ Rapport LaTeX et soutenance

**Limite ouverte :** le taux préférentiel effectivement appliqué au Maroc n'est pas
accessible via les APIs publiques sans clé. Il conditionne toute estimation causale de
l'effet tarifaire.

---

**Document créé le :** 10 novembre 2026  
**Dernière mise à jour :** 11 novembre 2026  
**Statut :** Version 2.0 — données réelles, projet terminé
