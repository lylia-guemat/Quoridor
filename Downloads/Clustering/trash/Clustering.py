import Fonctions
# === Importation des librairies nécessaires ===
import pandas as pd  # Pour manipuler les données tabulaires
from sklearn.feature_extraction.text import TfidfVectorizer  # Pour transformer le texte en vecteurs numériques
from sklearn.cluster import KMeans  # Pour faire du clustering non supervisé
from sklearn.decomposition import PCA  # Pour réduire la dimension des données (visualisation)
import matplotlib.pyplot as plt  # Pour générer des graphiques
import numpy as np  # Pour le calcul scientifique
import re

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
stop_fr = stopwords.words('french')


mots_trop_frequents = ['fonctionne', 'gauche', 'reprendre', 'prise', 'fixation','fixer', 'reprendre','fixation', 'fixée','fixé']


pd.set_option('display.max_colwidth', None)
import pandas as pd

df = pd.read_csv("RATPMRB.csv")

# On garde seulement les titres uniques, puis on applique la fonction de nettoyage à la colonne TITRE
titres_uniques = (
    df.drop_duplicates(subset=['TITRE'])['TITRE']
    .dropna()
    .apply(Fonctions.nettoyer_texte)
)

print(titres_uniques.shape)
print(titres_uniques)

print(" === 1. Charger les données depuis un fichier CSV === \n")
df = pd.read_csv("RATPMRB.csv").drop_duplicates(subset=['OBSERVATIONS'])
print(f"Les colonnes de la dataFrame : {df.columns}")

# print(" === 2. Nettoyage simple des textes (colonne OBSERVATIONS) ===\n")


# # Mise en minuscules + suppression de la ponctuation

# df['description_clean'] = df['OBSERVATIONS'].fillna("").str.lower().str.replace(r'[^\w\s]', '', regex=True)

# df = df[df['description_clean'].apply(Fonctions.est_texte_valide)]


# print(" === 3. Transformation des textes en vecteurs numériques (TF-IDF) ===\n")

# vectorizer = TfidfVectorizer(stop_words=stop_fr + mots_trop_frequents)
# X = vectorizer.fit_transform(df['description_clean'])  # Produit une matrice sparse ( documents x termes)
# print("\n ", X)

# print(" === 4. Application de KMeans pour créer des groupes de textes similaires ===\n")
# k = 8  # Nombre de clusters (groupes) à créer
# model = KMeans(n_clusters=k, random_state=42)  # Modèle KMeans
# model.fit(X)  # Apprentissage des centres des clusters

# # Ajout des étiquettes de cluster au DataFrame
# df['cluster'] = model.labels_  # Chaque description est affectée à un cluster (0, 1, ..., k-1)

# print(" === 5. Extraction des mots-clés dominants dans chaque cluster ===\n")
# terms = vectorizer.get_feature_names_out()  # Récupère la liste des termes (mots) utilisés
# print("vectorizer : \n",vectorizer )
# print ("models : \n",model.labels_)
# print("terms : \n",terms )


# # Applique la fonction pour extraire les mots-clés dominants
# cluster_keywords = Fonctions.get_top_keywords(X, model.labels_,terms)


# # Création d’un dictionnaire {cluster_label: "mot1 mot2 mot3"}
# cluster_names = {
#     label: ' '.join(keywords)
#     for label, keywords in zip(np.unique(model.labels_), cluster_keywords)
# }

# print (" cluster_names \n",cluster_names)
# # Ajout de la colonne avec les noms des clusters
# df['cluster_nom'] = df['cluster'].map(cluster_names)

# # Affichage d'exemples pour chaque cluster
# print(" === 6. Exemples par groupe d’anomalies ===\n")

# with open("clusters_exemples20.txt", "w", encoding="utf-8") as f:
#     for label in sorted(cluster_names):
#         f.write(f"\n--- Cluster {label} ({cluster_names[label]}) ---\n")

#         exemples = df[df['cluster'] == label]['description_clean'].head(20).tolist()
        
#         for i, texte in enumerate(exemples, start=1):
#             f.write(f"{i}. {texte.strip()}\n")

# print(" === 7. Visualisation des clusters en 2D via réduction de dimension (PCA) ===\n")
# # 1. Réduction initiale avec PCA
# X_pca = PCA(n_components=50, random_state=42).fit_transform(X.toarray())  # Réduction à 50 dimensions

# # 2. Réduction finale avec TSNE
# from sklearn.manifold import TSNE
# reduced = TSNE(n_components=2, random_state=42, perplexity=40, learning_rate=200, n_iter=1000).fit_transform(X_pca)

# # Visualisation
# plt.figure(figsize=(8, 6))
# scatter = plt.scatter(reduced[:, 0], reduced[:, 1], c=model.labels_, cmap='tab10')  # Points colorés par cluster

# # Ajouter les noms des clusters dans le graphique
# for i in range(k):
#     x_mean = reduced[model.labels_ == i][:, 0].mean()
#     y_mean = reduced[model.labels_ == i][:, 1].mean()
#     plt.text(x_mean, y_mean, f"{i}", fontsize=12, weight='bold', color='black', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))

# plt.legend(*scatter.legend_elements(), title="Clusters")
# plt.title("Visualisation des clusters d’anomalies")
# plt.xlabel("Dimension 1 (PCA + TSNE)")
# plt.ylabel("Dimension 2 (PCA + TSNE)")
# plt.grid(True)
# plt.tight_layout()

# # Sauvegarder l'image
# plt.savefig("images/visualisation_clustersk=7.png", dpi=300)

# # Affichage (optionnel)
# plt.show()