# 🚀 Guide de démarrage rapide - Jours 2-3

## ✅ Ce qui a déjà été fait (J1-J2)

1. ✅ Cadrage du projet complet
2. ✅ Choix du produit : Tomates marocaines (HS 0702)
3. ✅ Identification des sources de données
4. ✅ Question de recherche formulée
5. ✅ Structure du projet créée
6. ✅ Notebook template prêt
7. ✅ Script d'extraction développé
8. ✅ Documentation README complète

---

## 🎯 Prochaines étapes immédiates (J2-J3)

### Étape 1 : Tester l'accès à l'API UN Comtrade

```bash
cd ~/projet_barriere_tarifaire

# Activer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Test rapide de l'API
python3 -c "
import requests
url = 'https://comtradeapi.un.org/public/v1/preview/C/A/HS'
params = {
    'reporterCode': '504',
    'partnerCode': '0',
    'cmdCode': 'TOTAL',
    'flowCode': 'X',
    'period': '2023'
}
response = requests.get(url, params=params, timeout=30)
print('Statut API:', response.status_code)
if response.status_code == 200:
    data = response.json()
    print('Nombre d\'observations:', len(data.get('data', [])))
    print('✓ API accessible')
else:
    print('✗ Problème d\'accès')
"
```

### Étape 2 : Extraire les données

```bash
# Exécuter le script d'extraction
python scripts/extract_comtrade.py
```

**Temps estimé :** 5-10 minutes (selon connexion)

**Résultat attendu :**
- Fichier `data/raw/comtrade_maroc_tomates_2010_2023.csv`
- Fichier de métadonnées JSON
- Log d'extraction

### Étape 3 : Vérifier les données extraites

```bash
# Afficher les premières lignes
python3 -c "
import pandas as pd
df = pd.read_csv('data/raw/comtrade_maroc_tomates_2010_2023.csv')
print('Dimensions:', df.shape)
print('\nColonnes:', list(df.columns))
print('\nAperçu:')
print(df.head())
print('\nAnnées:', sorted(df['period'].unique()))
print('Nombre de partenaires:', df['partnerCode'].nunique())
"
```

### Étape 4 : Identifier les 10 principaux partenaires

```python
import pandas as pd

df = pd.read_csv('data/raw/comtrade_maroc_tomates_2010_2023.csv')

# Top 10 destinations
top10 = df.groupby(['partnerCode', 'partnerDesc'])['primaryValue'].sum()
top10 = top10.sort_values(ascending=False).head(10)

print("Top 10 destinations des tomates marocaines:")
print(top10)

# Sauvegarder la liste
top10.to_csv('data/processed/top10_partners.csv')
```

### Étape 5 : Accéder aux données tarifaires WTO (J3)

**Option 1 : API WTO (si disponible)**

```python
# Exemple de structure (à adapter selon l'API réelle)
import requests

wto_url = "https://api.wto.org/tariffs"
# Documentation : https://apiportal.wto.org/
```

**Option 2 : Téléchargement manuel**

1. Aller sur https://tao.wto.org/
2. Sélectionner :
   - Product : HS 0702
   - Importing countries : [Liste des top 10]
   - Years : 2010-2023
3. Télécharger en CSV
4. Sauvegarder dans `data/raw/wto_tariffs.csv`

**Option 3 : Données simulées (si bloqué)**

```python
import pandas as pd
import numpy as np

# UNIQUEMENT si l'accès WTO est impossible
# Simuler des tarifs réalistes basés sur la littérature

partners = ['France', 'Espagne', 'Allemagne', 'Russie', 'UK', 
            'Pays-Bas', 'Belgique', 'Italie', 'Pologne', 'USA']

# Tarifs moyens UE : 0-14.4% selon saison
# Tarifs Russie : ~15-20%
# Tarifs USA : ~3-5%

tariffs = {
    'France': 8.5,      # UE avec accord préférentiel
    'Espagne': 8.5,
    'Allemagne': 8.5,
    'Pays-Bas': 8.5,
    'Belgique': 8.5,
    'Italie': 8.5,
    'UK': 10.0,         # Après Brexit
    'Pologne': 8.5,     # UE
    'Russie': 15.0,     # Hors quotas
    'USA': 4.0
}

df_tariffs = pd.DataFrame([
    {'country': k, 'tariff_rate': v, 'preferential': v < 10}
    for k, v in tariffs.items()
])

print(df_tariffs)
```

---

## 📋 Checklist J2-J3

### Jour 2
- [ ] Installer l'environnement Python
- [ ] Tester l'accès API UN Comtrade
- [ ] Exécuter `extract_comtrade.py`
- [ ] Vérifier les données extraites
- [ ] Identifier les top 10 partenaires

### Jour 3
- [ ] Rechercher les données tarifaires WTO
- [ ] Compléter le dictionnaire des variables
- [ ] Fusionner les données commerciales et tarifaires
- [ ] Créer le fichier `data/processed/dataset_merged.csv`
- [ ] Documenter les sources dans le notebook

---

## 🔧 En cas de problème

### Problème 1 : API UN Comtrade inaccessible

**Solution :**
- Utiliser les données d'exemple du cours (si fournies)
- Télécharger manuellement depuis https://comtradeplus.un.org/
- Documenter clairement la limitation dans le rapport

### Problème 2 : Quotas API dépassés

**Solution :**
- Attendre 1 heure
- Réduire la plage d'années (ex: 2015-2023 au lieu de 2010-2023)
- Limiter aux top 5 partenaires au lieu de tous

### Problème 3 : Données tarifaires WTO inaccessibles

**Solution :**
1. Essayer TRAINS (UNCTAD) : https://trainsonline.unctad.org/
2. Consulter les accords de libre-échange Maroc-UE (publics)
3. Utiliser des tarifs moyens de la littérature académique
4. **Documenter clairement** la source et les limitations

---

## 📊 Structure attendue du dataset final

Après fusion, votre dataset doit ressembler à :

| period | reporterCode | partnerCode | partnerDesc | cmdCode | primaryValue | netWgt | tariff_rate | preferential | gdp_partner | distance |
|--------|--------------|-------------|-------------|---------|--------------|--------|-------------|--------------|-------------|----------|
| 2010 | 504 | 251 | France | 0702 | 25000000 | 15000000 | 8.5 | 1 | 2.6e12 | 1850 |
| 2010 | 504 | 643 | Russie | 0702 | 12000000 | 8000000 | 15.0 | 0 | 1.5e12 | 3500 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**Variables clés :**
- `primaryValue` : Valeur en USD (variable cible)
- `netWgt` : Poids en kg (variable cible alternative)
- `tariff_rate` : Taux de droit de douane en %
- `preferential` : 1 si accord préférentiel, 0 sinon

---

## 📝 Livrables J2-J3

1. ✅ Fichier CSV : `data/raw/comtrade_maroc_tomates_2010_2023.csv`
2. ⏳ Fichier CSV : `data/raw/wto_tariffs.csv` (ou équivalent)
3. ⏳ Fichier fusionné : `data/processed/dataset_merged.csv`
4. ⏳ Tableau : Dictionnaire des variables (dans le notebook)
5. ⏳ Documentation : Journal des sources dans `data/logs/sources.md`

---

## 🎯 Validation de l'étape J2-J3

Vous êtes prêt pour J4 (nettoyage) si :
- ✅ Vous avez un fichier CSV avec des données commerciales
- ✅ Vous avez identifié les principaux partenaires
- ✅ Vous avez au moins des tarifs indicatifs (réels ou littérature)
- ✅ Les variables sont documentées dans un dictionnaire
- ✅ Vous pouvez charger les données dans Pandas sans erreur

---

## 📞 Questions fréquentes

**Q : Faut-il absolument avoir les données 2010-2023 ?**
R : Non, 2015-2023 est suffisant (8 ans). Documentez la période.

**Q : Que faire si certains partenaires n'ont pas de données tarifaires ?**
R : Concentrez-vous sur les top 5-7 avec données complètes. Documentez les exclusions.

**Q : Peut-on utiliser des tarifs moyens au lieu de tarifs annuels ?**
R : Oui, si les tarifs varient peu dans le temps. Justifiez dans le rapport.

**Q : L'API ne répond pas, que faire ?**
R : Essayez l'interface web https://comtradeplus.un.org/ pour téléchargement manuel.

---

**Bon courage pour J2-J3 ! 🚀**

La partie la plus difficile (cadrage) est faite. L'extraction de données est maintenant mécanique.

Si vous êtes bloqué > 30 minutes sur un point, documentez le problème et passez à la suite.  
Vous pourrez revenir dessus avec l'encadrant.

---

**Prochaine mise à jour :** Guide J4-J5 (Nettoyage + EDA)
