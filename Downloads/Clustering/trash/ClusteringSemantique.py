import Fonctions
# === Importation des librairies nécessaires ===
import pandas as pd  # Pour manipuler les données tabulaires
from sklearn.feature_extraction.text import TfidfVectorizer  # Pour transformer le texte en vecteurs numériques
from sklearn.cluster import KMeans  # Pour faire du clustering non supervisé
from sklearn.decomposition import PCA  # Pour réduire la dimension des données (visualisation)
import matplotlib.pyplot as plt  # Pour générer des graphiques
import numpy as np  # Pour le calcul scientifique

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
stop_fr = stopwords.words('french')


print(" === 1. Charger les données depuis un fichier CSV === \n")
df = pd.read_csv("RATPMRB.csv").drop_duplicates(subset=['OBSERVATIONS'])
print(f"Les colonnes de la dataFrame : {df.columns}")

print(" === 2. Nettoyage simple des textes (colonne OBSERVATIONS) ===\n")
# Mise en minuscules + suppression de la ponctuation
df['description_clean'] = df['OBSERVATIONS'].fillna("").str.lower().str.replace(r'[^\w\s]', '', regex=True)

df = df[df['description_clean'].apply(est_texte_valide)]

