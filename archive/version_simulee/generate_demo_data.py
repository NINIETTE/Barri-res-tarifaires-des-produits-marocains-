#!/usr/bin/env python3
"""
Génération de données de démonstration réalistes
Projet : Barrières tarifaires sur les exportations marocaines de tomates

IMPORTANT : Ces données sont simulées mais basées sur :
- Statistiques officielles FAO et UN Comtrade (tendances générales)
- Tarifs réels documentés (accords UE-Maroc, tarifs russes, etc.)
- Structure de données conforme à UN Comtrade

À REMPLACER par les données réelles dès que l'API est accessible.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json

np.random.seed(42)

# Configuration
ANNEE_DEBUT = 2010
ANNEE_FIN = 2023
REPORTER_CODE = 504  # Maroc

# Principaux partenaires commerciaux du Maroc pour les tomates (sources : FAO, ITC)
PARTNERS = {
    'France': {'code': 251, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.25},
    'Espagne': {'code': 724, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.15},
    'Pays-Bas': {'code': 528, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.18},
    'Allemagne': {'code': 276, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.12},
    'Royaume-Uni': {'code': 826, 'region': 'EU', 'tariff_base': 10.0, 'preferential': False, 'share': 0.08},  # Post-Brexit
    'Russie': {'code': 643, 'region': 'Other', 'tariff_base': 15.0, 'preferential': False, 'share': 0.10},
    'Belgique': {'code': 56, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.05},
    'Italie': {'code': 380, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.03},
    'Pologne': {'code': 616, 'region': 'EU', 'tariff_base': 8.5, 'preferential': True, 'share': 0.02},
    'USA': {'code': 842, 'region': 'Other', 'tariff_base': 4.0, 'preferential': False, 'share': 0.02}
}

# PIB des pays (milliards USD, valeurs approximatives 2020)
GDP_DATA = {
    251: 2600,  # France
    724: 1280,  # Espagne
    528: 900,   # Pays-Bas
    276: 3800,  # Allemagne
    826: 2700,  # UK
    643: 1480,  # Russie
    56: 530,    # Belgique
    380: 1880,  # Italie
    616: 595,   # Pologne
    842: 21000  # USA
}

# Distance du Maroc (km approximatifs)
DISTANCE = {
    251: 1850,  # France
    724: 1200,  # Espagne
    528: 2200,  # Pays-Bas
    276: 2400,  # Allemagne
    826: 2100,  # UK
    643: 3500,  # Russie
    56: 2000,   # Belgique
    380: 2300,  # Italie
    616: 3000,  # Pologne
    842: 6200   # USA
}

def generate_realistic_data():
    """
    Génère des données de commerce réalistes
    
    Logique :
    - Croissance générale des exportations 2010-2019
    - Impact COVID (baisse 2020)
    - Reprise 2021-2023
    - Effet des tarifs : élasticité négative
    - Effet du PIB : élasticité positive
    - Effet distance : élasticité négative
    """
    
    all_data = []
    
    # Valeur totale de base (millions USD) - source : statistiques FAO
    base_export = 250  # Million USD en 2010
    
    for year in range(ANNEE_DEBUT, ANNEE_FIN + 1):
        # Tendance temporelle
        year_index = year - ANNEE_DEBUT
        
        # Croissance générale : +5% par an jusqu'à 2019, choc COVID 2020, reprise ensuite
        if year <= 2019:
            growth_factor = (1.05) ** year_index
        elif year == 2020:
            growth_factor = (1.05) ** 9 * 0.85  # Choc COVID -15%
        elif year == 2021:
            growth_factor = (1.05) ** 9 * 0.90  # Reprise partielle
        else:
            growth_factor = (1.05) ** 9 * (1.08) ** (year - 2021)  # Forte reprise
        
        total_value_year = base_export * growth_factor
        
        for partner_name, partner_info in PARTNERS.items():
            partner_code = partner_info['code']
            share = partner_info['share']
            
            # Valeur de base pour ce partenaire
            partner_value = total_value_year * share
            
            # Effet du tarif (élasticité -0.8)
            tariff = partner_info['tariff_base']
            if partner_name == 'Royaume-Uni' and year >= 2021:
                tariff = 10.0  # Brexit
            
            tariff_effect = (1 - 0.008 * tariff)  # Élasticité -0.8
            
            # Effet accord préférentiel (+15%)
            preferential_effect = 1.15 if partner_info['preferential'] else 1.0
            
            # Effet distance (élasticité -0.3)
            distance_km = DISTANCE[partner_code]
            distance_effect = (2000 / distance_km) ** 0.3
            
            # Effet PIB (élasticité +0.5)
            gdp = GDP_DATA[partner_code] * (1.02) ** year_index  # Croissance PIB 2%/an
            gdp_effect = (gdp / 1000) ** 0.2
            
            # Calcul valeur finale
            final_value = (partner_value * 
                          tariff_effect * 
                          preferential_effect * 
                          distance_effect * 
                          gdp_effect)
            
            # Ajouter du bruit réaliste
            noise = np.random.normal(1, 0.08)
            final_value *= noise
            
            # Conversion en kg (poids net) - prix moyen 0.8 USD/kg
            net_weight = final_value / 0.8 * 1e6  # en kg
            
            # Créer l'observation
            observation = {
                'period': year,
                'reporterCode': REPORTER_CODE,
                'reporterDesc': 'Morocco',
                'partnerCode': partner_code,
                'partnerDesc': partner_name,
                'flowCode': 'X',
                'flowDesc': 'Export',
                'cmdCode': '0702',
                'cmdDesc': 'Tomatoes, fresh or chilled',
                'primaryValue': round(final_value * 1e6, 2),  # USD
                'netWgt': round(net_weight, 2),  # kg
                'tariff_rate': tariff,
                'preferential_agreement': int(partner_info['preferential']),
                'gdp_partner': round(gdp * 1e9, 2),  # USD
                'distance_km': distance_km,
                'region': partner_info['region']
            }
            
            all_data.append(observation)
    
    return pd.DataFrame(all_data)


def add_derived_variables(df):
    """Ajoute les variables dérivées pour l'analyse"""
    
    # Logarithmes
    df['log_value'] = np.log(df['primaryValue'] + 1)
    df['log_weight'] = np.log(df['netWgt'] + 1)
    df['log_gdp'] = np.log(df['gdp_partner'])
    df['log_distance'] = np.log(df['distance_km'])
    
    # Variables binaires
    df['high_tariff'] = (df['tariff_rate'] > 10).astype(int)
    df['eu_member'] = (df['region'] == 'EU').astype(int)
    
    # Tendance temporelle
    df['trend'] = df['period'] - df['period'].min()
    
    # Variables décalées (lag) par pays
    df = df.sort_values(['partnerCode', 'period'])
    df['lag_value'] = df.groupby('partnerCode')['primaryValue'].shift(1)
    df['lag_weight'] = df.groupby('partnerCode')['netWgt'].shift(1)
    
    # Taux de croissance
    df['growth_rate'] = ((df['primaryValue'] - df['lag_value']) / df['lag_value'] * 100).round(2)
    
    return df


def main():
    """Fonction principale"""
    
    print("=" * 70)
    print("GÉNÉRATION DE DONNÉES DE DÉMONSTRATION")
    print("Projet : Barrières tarifaires - Tomates marocaines")
    print("=" * 70)
    
    print("\n⚠️  IMPORTANT :")
    print("Ces données sont SIMULÉES mais réalistes (basées sur statistiques FAO/ITC)")
    print("À remplacer par données UN Comtrade réelles dès que l'API est accessible\n")
    
    # Générer les données
    print("1. Génération des données de base...")
    df = generate_realistic_data()
    print(f"   ✓ {len(df)} observations générées ({ANNEE_DEBUT}-{ANNEE_FIN})")
    print(f"   ✓ {df['partnerCode'].nunique()} partenaires commerciaux")
    
    # Ajouter variables dérivées
    print("\n2. Ajout des variables dérivées...")
    df = add_derived_variables(df)
    print(f"   ✓ {len(df.columns)} variables au total")
    
    # Sauvegarder données brutes
    print("\n3. Sauvegarde des données...")
    raw_file = f"../data/raw/comtrade_maroc_tomates_{ANNEE_DEBUT}_{ANNEE_FIN}.csv"
    df.to_csv(raw_file, index=False, encoding='utf-8')
    print(f"   ✓ Données brutes : {raw_file}")
    
    # Sauvegarder données processées
    processed_file = f"../data/processed/dataset_merged.csv"
    df.to_csv(processed_file, index=False, encoding='utf-8')
    print(f"   ✓ Données processées : {processed_file}")
    
    # Métadonnées
    print("\n4. Génération des métadonnées...")
    metadata = {
        'date_generation': datetime.now().isoformat(),
        'type': 'DONNÉES SIMULÉES - Remplacer par données réelles',
        'source_reference': 'Basé sur statistiques FAO, ITC, et tarifs documentés',
        'reporter': f"Maroc (code {REPORTER_CODE})",
        'commodity': "Tomates HS 0702",
        'flow': 'Exportations',
        'period': f"{ANNEE_DEBUT}-{ANNEE_FIN}",
        'nb_observations': len(df),
        'nb_annees': df['period'].nunique(),
        'nb_partenaires': df['partnerCode'].nunique(),
        'partners': list(PARTNERS.keys()),
        'variables': list(df.columns),
        'valeur_totale_2023_millions_usd': round(df[df['period']==2023]['primaryValue'].sum()/1e6, 2),
        'note': 'Données générées avec élasticités réalistes : tarif=-0.8, PIB=+0.5, distance=-0.3'
    }
    
    metadata_file = "../data/raw/metadata_demo.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"   ✓ Métadonnées : {metadata_file}")
    
    # Statistiques descriptives
    print("\n" + "=" * 70)
    print("STATISTIQUES DESCRIPTIVES")
    print("=" * 70)
    
    print(f"\nDimensions : {df.shape}")
    print(f"Période : {df['period'].min()} - {df['period'].max()}")
    print(f"Nombre de partenaires : {df['partnerCode'].nunique()}")
    
    print("\nTop 5 destinations (valeur totale 2010-2023) :")
    top5 = df.groupby('partnerDesc')['primaryValue'].sum().sort_values(ascending=False).head(5)
    for i, (country, value) in enumerate(top5.items(), 1):
        print(f"  {i}. {country:15s} : {value/1e6:8.2f} M USD")
    
    print("\nÉvolution temporelle (valeur totale en millions USD) :")
    evolution = df.groupby('period')['primaryValue'].sum() / 1e6
    for year in [2010, 2015, 2020, 2023]:
        if year in evolution.index:
            print(f"  {year} : {evolution[year]:8.2f} M USD")
    
    print("\nTarifs appliqués :")
    tariffs = df.groupby('partnerDesc')['tariff_rate'].first().sort_values()
    for country, tariff in tariffs.items():
        pref = " (accord préférentiel)" if df[df['partnerDesc']==country]['preferential_agreement'].iloc[0] else ""
        print(f"  {country:15s} : {tariff:5.1f}%{pref}")
    
    print("\n" + "=" * 70)
    print("GÉNÉRATION TERMINÉE")
    print("=" * 70)
    print(f"\n✓ Fichiers créés dans ../data/")
    print(f"✓ Prêt pour l'analyse exploratoire (J4-J5)")
    
    # Aperçu
    print("\nAperçu des données :")
    print(df.head(10).to_string())
    
    return df


if __name__ == "__main__":
    df = main()
