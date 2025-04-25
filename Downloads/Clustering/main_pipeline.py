# === Importation des librairies nécessaires ===
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import numpy as np
import nltk
from nltk.corpus import stopwords
from clustering_utils import *

# === Configuration ===
nltk.download('stopwords')

FICHIER_CSV = "RATPMRB.csv"
COLONNE_TEXTE = "OBSERVATIONS"

STOPWORDS_FR = stopwords.words('french')
MOTS_SUPPRIMER = ['fonctionne', 'gauche', 'reprendre', 'prise', 'fixation', 'fixer', 'fixée', 'fixé', 'test', 'tester']

# Différente valeurs de k pour l'entrainement 
K_VALUES = [4, 6, 8, 10]


def pipeline_clustering(k):
    print(f"\n====== Pipeline pour k = {k} clusters ======\n")

    df = charger_donnees(FICHIER_CSV, COLONNE_TEXTE)
    # df = appliquer_nettoyage(df, COLONNE_TEXTE)
    # X, vectorizer = vectoriser_textes(df['description_clean'], STOPWORDS)

    df = charger_donnees(FICHIER_CSV, COLONNE_TEXTE)
    df = appliquer_nettoyage(df, COLONNE_TEXTE)

    # Construire les stopwords dynamiquement avec les textes du dataset
    STOPWORDS = construire_stopwords(df['description_clean'].tolist() + STOPWORDS_FR + MOTS_SUPPRIMER)

    X, vectorizer = vectoriser_textes(df['description_clean'], STOPWORDS)

    model = clusteriser_textes(X, k)
    df['cluster'] = model.labels_

    # Évaluation du modèle
    silhouette, calinski, davies = evaluer_modeles(X, model.labels_)
    enregistrer_scores(k, silhouette, calinski, davies)


    terms = vectorizer.get_feature_names_out()
    cluster_keywords = get_top_keywords(X, model.labels_, terms)
    cluster_names = {label: ' '.join(kw) for label, kw in zip(np.unique(model.labels_), cluster_keywords)}
    df['cluster_nom'] = df['cluster'].map(cluster_names)

    # Sauvegarde fichiers
    sauvegarder_exemples(df, cluster_names, suffix=f"k_{k}")
    visualiser_clusters(X, model.labels_, k, titre=f"Clusters (k={k})", filename=f"images/visualisation_k{k}.png")
    df.to_csv(f"cluster_csv/resultats_k{k}.csv", index=False, encoding="utf-8")

    model = clusteriser_textes(X, k)
    df['cluster'] = model.labels_

  

    return df


# === Lancement ===
if __name__ == "__main__":
    for k in K_VALUES:
        df_resultat = pipeline_clustering(k)

if __name__ == "__main__":
    for k in K_VALUES:
        pipeline_clustering(k)

    visualiser_scores()
