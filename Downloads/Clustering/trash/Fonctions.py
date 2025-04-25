import numpy as np  # Pour le calcul scientifique
import re
import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans

# Nettoyage de texte simple
def nettoyer_texte(texte):
    texte = texte.lower()
    texte = re.sub(r'[^\w\s]', '', texte)
    return texte

# Nettoyage de texte avancée

def est_texte_valide(texte):
    texte = str(texte).strip().lower()
    
    # Trop court en caractères
    if len(texte) < 10:
        return False
    
    # Trop peu de mots
    if len(texte.split()) < 3:
        return False
    
    # Texte avec trop de répétitions (ex: "aaaaaaa", "bbb bbb bbb")
    lettres_uniques = set(re.sub(r'[^a-zA-Z]', '', texte))  # on garde que les lettres
    if len(lettres_uniques) <= 3:
        return False
    
    return True


def appliquer_nettoyage(df, colonne_texte):
    df['description_clean'] = df[colonne_texte].fillna("").apply(nettoyer_texte)
    return df

# Chargement des données
def charger_donnees(fichier, colonne_texte):
    df = pd.read_csv(fichier).drop_duplicates(subset=[colonne_texte])
    df[colonne_texte] = df[colonne_texte].fillna("")
    return df

# Vectorisation
def vectoriser_textes(textes, stopwords):
    vectorizer = TfidfVectorizer(stop_words=stopwords)
    X = vectorizer.fit_transform(textes)
    return X, vectorizer

# Clustering
def clusteriser_textes(X, n_clusters):
    model = KMeans(n_clusters=n_clusters, random_state=42)
    model.fit(X)
    return model

# Mots-clés par cluster
def get_top_keywords(X, labels, terms, n_terms=10):
    df_keywords = pd.DataFrame(X.todense()).groupby(labels).mean()
    keywords = []
    for i, row in df_keywords.iterrows():
        top_terms = row.argsort()[-n_terms:][::-1]
        keywords.append([terms[i] for i in top_terms])
    return keywords

# Sauvegarde des exemples
def sauvegarder_exemples(df, cluster_names, output_file="clusters_exemples20.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        for label in sorted(cluster_names):
            f.write(f"\n--- Cluster {label} ({cluster_names[label]}) ---\n")
            exemples = df[df['cluster'] == label]['description_clean'].head(20)
            for i, texte in enumerate(exemples, start=1):
                f.write(f"{i}. {texte.strip()}\n")

# Visualisation
def visualiser_clusters(X, labels, n_clusters, titre="Clusters", filename="images/clusters.png"):
    X_pca = PCA(n_components=50).fit_transform(X.toarray())
    reduced = TSNE(n_components=2, random_state=42, perplexity=40, learning_rate=200).fit_transform(X_pca)

    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(reduced[:, 0], reduced[:, 1], c=labels, cmap='tab10')

    for i in range(n_clusters):
        x_mean = reduced[labels == i][:, 0].mean()
        y_mean = reduced[labels == i][:, 1].mean()
        plt.text(x_mean, y_mean, f"{i}", fontsize=12, weight='bold',
                 color='black', bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))

    plt.title(titre)
    plt.xlabel("Dimension 1 (PCA + TSNE)")
    plt.ylabel("Dimension 2 (PCA + TSNE)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()


def get_top_keywords(X, labels, terms, n_top=10):
    
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


