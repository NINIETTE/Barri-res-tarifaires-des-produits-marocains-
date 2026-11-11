#!/usr/bin/env python3
"""
Script d'extraction des données UN Comtrade
Projet : Barrières tarifaires sur les exportations marocaines de tomates
Auteur : [À compléter]
Date : 10 novembre 2026
"""

import pandas as pd
import requests
import time
import json
from pathlib import Path
from datetime import datetime

# Configuration
BASE_URL = 'https://comtradeapi.un.org/public/v1/preview/C/A/HS'
REPORTER_MAROC = '504'
HS_CODE_TOMATES = '0702'
FLOW_EXPORT = 'X'
ANNEE_DEBUT = 2010
ANNEE_FIN = 2023
DELAI_ENTRE_REQUETES = 1.5  # secondes (respecter les quotas)

# Dossiers
DATA_DIR = Path(__file__).parent.parent / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'
LOGS_DIR = DATA_DIR / 'logs'

# Créer les dossiers si inexistants
for directory in [RAW_DIR, PROCESSED_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


class ComtradeExtractor:
    """Classe pour extraire les données UN Comtrade"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.log_file = LOGS_DIR / f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message):
        """Enregistre un message dans le fichier de log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def fetch_year(self, reporter, partner, commodity, flow, period):
        """
        Extrait les données pour une année donnée
        
        Parameters:
        -----------
        reporter : str - Code pays exportateur
        partner : str - Code pays importateur ('0' pour tous)
        commodity : str - Code HS
        flow : str - 'X' pour export, 'M' pour import
        period : int - Année
        
        Returns:
        --------
        pd.DataFrame ou None
        """
        params = {
            'reporterCode': reporter,
            'partnerCode': partner,
            'cmdCode': commodity,
            'flowCode': flow,
            'period': str(period)
        }
        
        try:
            self.log(f"Requête pour l'année {period}...")
            response = self.session.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'])
                self.log(f"✓ {period} : {len(df)} observations extraites")
                return df
            else:
                self.log(f"⚠ {period} : Aucune donnée disponible")
                return None
        
        except requests.exceptions.HTTPError as e:
            self.log(f"✗ {period} : Erreur HTTP {e}")
            return None
        except requests.exceptions.Timeout:
            self.log(f"✗ {period} : Timeout de la requête")
            return None
        except requests.exceptions.RequestException as e:
            self.log(f"✗ {period} : Erreur de requête {e}")
            return None
        except json.JSONDecodeError:
            self.log(f"✗ {period} : Erreur de décodage JSON")
            return None
    
    def fetch_range(self, reporter, partner, commodity, flow, year_start, year_end):
        """
        Extrait les données pour une plage d'années
        
        Returns:
        --------
        pd.DataFrame - Données consolidées
        """
        all_data = []
        
        self.log(f"Début de l'extraction : {year_start}-{year_end}")
        self.log(f"Reporter: {reporter}, Partner: {partner}, Commodity: {commodity}, Flow: {flow}")
        
        for year in range(year_start, year_end + 1):
            df_year = self.fetch_year(reporter, partner, commodity, flow, year)
            
            if df_year is not None:
                all_data.append(df_year)
            
            # Pause pour respecter les limites de l'API
            time.sleep(DELAI_ENTRE_REQUETES)
        
        if all_data:
            df_combined = pd.concat(all_data, ignore_index=True)
            self.log(f"✓ Extraction terminée : {len(df_combined)} observations au total")
            return df_combined
        else:
            self.log("✗ Aucune donnée extraite")
            return pd.DataFrame()
    
    def save_raw_data(self, df, filename):
        """Sauvegarde les données brutes en CSV"""
        filepath = RAW_DIR / filename
        df.to_csv(filepath, index=False, encoding='utf-8')
        self.log(f"✓ Données sauvegardées : {filepath}")
        return filepath


def main():
    """Fonction principale d'extraction"""
    
    print("=" * 60)
    print("EXTRACTION DONNÉES UN COMTRADE")
    print("Projet : Barrières tarifaires - Tomates marocaines")
    print("=" * 60)
    
    # Initialiser l'extracteur
    extractor = ComtradeExtractor()
    
    # Extraction des données d'exportation du Maroc
    extractor.log("PHASE 1 : Extraction des exportations marocaines de tomates")
    
    df_export = extractor.fetch_range(
        reporter=REPORTER_MAROC,
        partner='0',  # Tous les partenaires
        commodity=HS_CODE_TOMATES,
        flow=FLOW_EXPORT,
        year_start=ANNEE_DEBUT,
        year_end=ANNEE_FIN
    )
    
    if not df_export.empty:
        # Sauvegarde
        filename = f"comtrade_maroc_tomates_{ANNEE_DEBUT}_{ANNEE_FIN}.csv"
        filepath = extractor.save_raw_data(df_export, filename)
        
        # Statistiques descriptives
        extractor.log("\n" + "=" * 60)
        extractor.log("STATISTIQUES DESCRIPTIVES")
        extractor.log("=" * 60)
        extractor.log(f"Dimensions : {df_export.shape}")
        extractor.log(f"Colonnes : {list(df_export.columns)}")
        extractor.log(f"Années couvertes : {df_export['period'].min()} - {df_export['period'].max()}")
        
        if 'partnerDesc' in df_export.columns:
            top_partners = df_export.groupby('partnerDesc')['primaryValue'].sum().sort_values(ascending=False).head(10)
            extractor.log("\nTop 10 pays importateurs (par valeur totale) :")
            for i, (country, value) in enumerate(top_partners.items(), 1):
                extractor.log(f"  {i}. {country}: {value/1e6:.2f} M USD")
        
        # Métadonnées
        metadata = {
            'date_extraction': datetime.now().isoformat(),
            'source': 'UN Comtrade API',
            'url': BASE_URL,
            'reporter': f"Maroc (code {REPORTER_MAROC})",
            'commodity': f"Tomates HS {HS_CODE_TOMATES}",
            'flow': 'Exportations',
            'period': f"{ANNEE_DEBUT}-{ANNEE_FIN}",
            'nb_observations': len(df_export),
            'nb_annees': df_export['period'].nunique(),
            'nb_partenaires': df_export['partnerCode'].nunique()
        }
        
        metadata_file = RAW_DIR / f"metadata_{ANNEE_DEBUT}_{ANNEE_FIN}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        extractor.log(f"\n✓ Métadonnées sauvegardées : {metadata_file}")
        
        print("\n" + "=" * 60)
        print("EXTRACTION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        print(f"Fichier de données : {filepath}")
        print(f"Fichier de log : {extractor.log_file}")
        print(f"Métadonnées : {metadata_file}")
        
        return df_export
    
    else:
        extractor.log("\n✗ ÉCHEC DE L'EXTRACTION")
        print("\nAucune donnée n'a pu être extraite. Vérifier :")
        print("1. La connexion internet")
        print("2. L'accès à l'API UN Comtrade")
        print("3. Les paramètres de la requête")
        print(f"\nConsulter le log : {extractor.log_file}")
        return None


if __name__ == "__main__":
    # Exécution
    df_result = main()
    
    # Affichage d'un échantillon si succès
    if df_result is not None and not df_result.empty:
        print("\n" + "=" * 60)
        print("APERÇU DES DONNÉES")
        print("=" * 60)
        print(df_result.head(10).to_string())
        print("\n" + "=" * 60)
        print("PROCHAINES ÉTAPES")
        print("=" * 60)
        print("1. Vérifier la qualité des données extraites")
        print("2. Extraire les données de tarifs (WTO)")
        print("3. Compléter le notebook avec ces données")
        print("4. Commencer l'analyse exploratoire (EDA)")
