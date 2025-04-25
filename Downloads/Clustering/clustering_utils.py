import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score,calinski_harabasz_score, davies_bouldin_score
import csv
import os



# Nettoyage de texte
def nettoyer_texte(texte):
    texte = texte.lower()
    texte = re.sub(r'[^\w\s]', '', texte)
    return texte



# Fonction pour construire la liste des mots à ignorer

def construire_stopwords(textes):
    stopwords_dynamiques = set()
    for texte in textes:
        texte = str(texte).strip().lower()
        texte = re.sub(r'[^\w\s]', '', texte)
        for mot in texte.split():
            if (
                len(mot) < 3 
                or not mot.isalpha() 
                or len(set(mot)) <= 2  # genre "aaaaaaa","bbbbb"
            ):
                stopwords_dynamiques.add(mot)
    return list(stopwords_dynamiques)



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



def sauvegarder_exemples(df, cluster_names, suffix=""):
    nom_fichier = f"exemple_fichier/clusters_exemples_{suffix}.txt" if suffix else "clusters_exemples.txt"
    with open(nom_fichier, "w", encoding="utf-8") as f:
        for label in sorted(cluster_names):
            f.write(f"\n--- Cluster {label} ({cluster_names[label]}) ---\n")
            exemples = df[df['cluster'] == label]['description_clean'].head(20).tolist()
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

    plt.legend(*scatter.legend_elements(), title="Clusters")

    plt.title(titre)
    plt.xlabel("Dimension 1 (PCA + TSNE)")
    plt.ylabel("Dimension 2 (PCA + TSNE)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.show()


# Evaluation de notre cluster

# === MÉTRIQUES D'ÉVALUATION DES CLUSTERS ===
# Ces métriques permettent d'évaluer la qualité des clusters créés par l'algorithme de clustering.
# Elles sont particulièrement utiles en l'absence de "vrais" labels (clustering non supervisé).

# 1. Silhouette Score
# ---------------------
# Valeurs possibles : entre -1 et 1
# - Proche de 1 : bon clustering, les points sont bien regroupés dans leur cluster et éloignés des autres.
# - Proche de 0 : les clusters se chevauchent, les points sont proches de la frontière.
# - Négatif : mauvais clustering, les points sont probablement dans le mauvais cluster.
# Cette métrique mesure à quel point un point est similaire à son propre cluster par rapport aux autres.

# 2. Calinski-Harabasz Index
# ---------------------------
# Valeurs possibles : [0, +∞), plus c’est grand, mieux c’est.
# - Évalue le rapport entre la dispersion inter-clusters et intra-clusters.
# - Un score élevé indique que les clusters sont denses et bien séparés.
# Idéal pour détecter des regroupements nets.

# 3. Davies-Bouldin Index
# -------------------------
# Valeurs possibles : [0, +∞), plus c’est petit, mieux c’est.
# - Mesure la similarité entre les clusters (en tenant compte de la distance moyenne intra-cluster).
# - Un score bas indique que les clusters sont compacts et bien distincts les uns des autres.





def evaluer_silhouette(X, labels):
    score = silhouette_score(X, labels)
    print(f"Silhouette Score: {score:.4f}")
    return score

def evaluer_calinski_harabasz(X, labels):
    score = calinski_harabasz_score(X.toarray(), labels)
    return score


def evaluer_davies_bouldin(X, labels):
    score = davies_bouldin_score(X.toarray(), labels)
    return score

def evaluer_calinski_harabasz(X, labels):
    score = calinski_harabasz_score(X.toarray(), labels)
    return score

def enregistrer_scores(k, silhouette, calinski, davies, fichier="scores_clustering.csv"):
    entetes = ["k", "silhouette", "calinski_harabasz", "davies_bouldin"]
    fichier_existe = os.path.exists(fichier)

    with open(fichier, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not fichier_existe:
            writer.writerow(entetes)
        writer.writerow([k, silhouette, calinski, davies])


def evaluer_modeles(X, labels):
    silhouette = evaluer_silhouette(X, labels)
    calinski = evaluer_calinski_harabasz(X, labels)
    davies = evaluer_davies_bouldin(X, labels)
    print(f"Silhouette Score: {silhouette:.4f}")
    print(f"Calinski-Harabasz Index: {calinski:.4f}")
    print(f"Davies-Bouldin Index: {davies:.4f}")
    return silhouette, calinski, davies

def visualiser_scores(fichier="scores_clustering.csv"):
    df_scores = pd.read_csv(fichier)
    plt.figure(figsize=(10, 6))

    plt.plot(df_scores["k"], df_scores["silhouette"], label="Silhouette", marker='o')
    plt.plot(df_scores["k"], df_scores["calinski_harabasz"], label="Calinski-Harabasz", marker='o')
    plt.plot(df_scores["k"], df_scores["davies_bouldin"], label="Davies-Bouldin", marker='o')

    plt.title("Évaluation des modèles de clustering")
    plt.xlabel("Nombre de clusters (k)")
    plt.ylabel("Score")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("images/evaluation_scores.png", dpi=300)
    plt.show()

