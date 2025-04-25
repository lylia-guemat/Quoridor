import pandas as pd
import re
import nltk
from nltk.corpus import stopwords

# Si ce n'est pas déjà fait, télécharge les stopwords de NLTK
nltk.download('stopwords')

# Fonction de nettoyage de texte
def clean_text(text):
    # 1. Supprimer les chiffres et les préfixes comme '0108', '253408', etc.
    text = re.sub(r'\b\d+\b', '', text)
    
    # 2. Enlever les mots inutiles (stopwords) et les symboles spéciaux
    stop_words = set(stopwords.words('french'))
    
    # Supprimer les caractères non alphabétiques, laisser uniquement les lettres et les espaces
    text = re.sub(r'[^a-zA-Zéèàêùôûîïç\s]', '', text)
    
    # 3. Convertir le texte en minuscules
    text = text.lower()
    
    # 4. Supprimer les stopwords
    text = ' '.join([word for word in text.split() if word not in stop_words])
    
    return text

# Fonction pour appliquer le nettoyage sur chaque ligne d'une liste de clusters

def clean_clusters(clusters):
    cleaned_clusters = []
    for cluster in clusters:
        if pd.isna(cluster):
            cleaned_clusters.append('')  # ou 'inconnu' si tu préfères
        else:
            cleaned_cluster = clean_text(str(cluster))
            cleaned_clusters.append(cleaned_cluster)
    return cleaned_clusters

# Exemple de données (remplacer avec tes propres données)
df= pd.read_csv("RATPMRB.CSV")
colonne = df["TITRE"]

# Appliquer le nettoyage sur tous les clusters
df['cluster_cleaned'] = clean_clusters(colonne)

# Afficher le résultat
print(df['cluster_cleaned'])
print(df)