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
df = pd.read_csv("RATPMRB.csv").drop_duplicates()  # Charge les données dans un DataFrame pandas

print(f"Les colonnes de la dataFrame : {df.columns}")

print(" === 2. Combiner plusieurs colonnes texte en une seule === \n")
# Affichage de la forme initiale de la colonne 'OBSERVATIONS'
colonnes_texte = df['OBSERVATIONS']
print(colonnes_texte.shape)




# Les colonnes de la dataFrame : Index(['code', 'name', 'parent (code)', 'parent', 'database (code)',
#        'database', 'created_at', 'updated_at', 'CAUSE',
#        'CORRECTION_CONSTRUCTEUR', 'OBSERVATIONS', 'OLS', 'PHOTO', 'PHOTO2',
#        'PHOTO3', 'PHOTO4', 'REPORT', 'RESERVE', 'RESULTAT_NOUVEAU_CONTROLE',
#        'TEXTE_CTRL', 'TITRE'],
#       dtype='object')



# Remplace les NaN par des chaînes vides, puis concatène
df['texte_combine'] = df[colonnes_texte].fillna('').agg(' '.join, axis=1)

# Nettoyage : supprime les séquences alphanumériques (ex : 00000, 0102reportpa01...)
# Supprime les espaces multiples, puis enlève les espaces en début/fin
# Et supprime les doublons d'espaces (pour éviter les "   " multiples)
df['texte_combine_clean'] = (
    df['texte_combine']
      .str.replace(r'\b[a-zA-Z0-9]{5,}\b', '', regex=True)  # Supprime les codes longs
      .str.replace(r'\s+', ' ', regex=True)                 # Supprime les espaces multiples
      .str.strip()                                          # Supprime les espaces en début/fin
      .str.replace(r'\s+', ' ', regex=True)                 # Assure qu'il n'y a pas d'espaces doubles restants
)

print(" === 3. Transformation des textes en vecteurs numériques (TF-IDF) ===\n")
vectorizer = TfidfVectorizer(stop_words=stop_fr)  # Retire les mots inutiles (stop words français)
X = vectorizer.fit_transform(df['texte_combine_clean'])  # Produit une matrice sparse ( documents x termes)
print("\n ", X)

print(" === 4. Application de KMeans pour créer des groupes de textes similaires ===\n")
k = 8  # Nombre de clusters (groupes) à créer
model = KMeans(n_clusters=k, random_state=42)  # Modèle KMeans
model.fit(X)  # Apprentissage des centres des clusters

# Ajout des étiquettes de cluster au DataFrame
df['cluster'] = model.labels_  # Chaque description est affectée à un cluster (0, 1, ..., k-1)

print(" === 5. Extraction des mots-clés dominants dans chaque cluster ===\n")
terms = vectorizer.get_feature_names_out()  # Récupère la liste des termes (mots) utilisés
print("vectorizer : \n",vectorizer )
print ("models : \n",model.labels_)
print("terms : \n",terms )
def get_top_keywords(X, labels, n_top=10):
    
    # Récupère les indices des mots les plus fréquents par cluster
    cluster_keywords = []
    for label in set(labels):  # On parcourt les différents clusters
        cluster_indices = [i for i, l in enumerate(labels) if l == label]  # Les indices du cluster

        # Moyenne des vecteurs TF-IDF des documents lignes dans le cluster
        cluster_center = X[cluster_indices].mean(axis=0)
        print("cluster_center \n", cluster_center)

        # Aplatir proprement le vecteur (de matrix -> array 1D)
        cluster_center_array = np.asarray(cluster_center).flatten()
        print("cluster_center_array \n", cluster_center_array)

        # Trie les indices en fonction de la valeur TF-IDF
        top_indices = cluster_center_array.argsort()[::-1][:n_top]  # N indices avec la plus haute valeur

        # Récupère les mots correspondants aux indices 
        top_terms = [terms[ind] for ind in reversed(top_indices)]

        cluster_keywords.append(top_terms)
    print ("cluster_keywords : \n",cluster_keywords)
    return cluster_keywords
# Applique la fonction pour extraire les mots-clés dominants
cluster_keywords = get_top_keywords(X, model.labels_)

# Création d’un dictionnaire {cluster_label: "mot1 mot2 mot3"}
cluster_names = {
    label: ' '.join(keywords)
    for label, keywords in zip(np.unique(model.labels_), cluster_keywords)
}

print (" cluster_names \n",cluster_names)
# Ajout de la colonne avec les noms des clusters
df['cluster_nom'] = df['cluster'].map(cluster_names)

# Affichage d'exemples pour chaque cluster
print(" === 6. Exemples par groupe d’anomalies ===\n")

with open("clusters_exemples.txt", "w", encoding="utf-8") as f:
    for label in sorted(cluster_names):
        f.write(f"\n--- Cluster {label} ({cluster_names[label]}) ---\n")
        exemples = df[df['cluster'] == label]['texte_combine_clean'].head(5).to_string(index=False)
        f.write(exemples + "\n")

print(" === 7. Visualisation des clusters en 2D via réduction de dimension (PCA) ===\n")
# reduced = PCA(n_components=2).fit_transform(X.toarray())  # Réduit les vecteurs à 2 dimensions
from sklearn.decomposition import TruncatedSVD

svd = TruncatedSVD(n_components=2, random_state=42)
reduced = svd.fit_transform(X)  # Pas besoin de .toarray()

plt.figure(figsize=(8, 6))
scatter = plt.scatter(reduced[:, 0], reduced[:, 1], c=model.labels_, cmap='tab10')  # Points colorés par cluster
plt.legend(*scatter.legend_elements(), title="Clusters")
plt.title("Visualisation des clusters d’anomalies")
plt.xlabel("PCA 1")
plt.ylabel("PCA 2")
plt.grid(True)
plt.tight_layout()
plt.show()
