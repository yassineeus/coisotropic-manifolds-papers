import arxiv
import pandas as pd
import datetime
import os
import yaml
from pathlib import Path

# Configuration
SEARCH_QUERY = 'coisotropic manifold OR "coisotropic submanifold" OR "coisotropic structure"'
MAX_RESULTS = 1000  # Nombre maximum d'articles à récupérer
RESULTS_FILE = "coisotropic_manifolds_database.csv"  # Fichier de stockage
README_FILE = "README.md"  # Fichier de présentation

def fetch_articles():
    """Récupère les articles depuis arXiv"""
    print(f"Recherche d'articles avec la requête: {SEARCH_QUERY}")
    
    # Créer un client avec une configuration personnalisée
    client = arxiv.Client(
        page_size=100,
        delay_seconds=3,
        num_retries=5
    )
    
    # Effectuer la recherche
    search = arxiv.Search(
        query=SEARCH_QUERY,
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # Récupérer les articles
    results = list(client.results(search))
    print(f"Nombre d'articles récupérés: {len(results)}")
    
    return results

def update_database(results):
    """Met à jour la base de données d'articles"""
    # Créer un DataFrame à partir des résultats
    articles = []
    
    for result in results:
        # Extraire les informations
        article_id = result.get_short_id()
        title = result.title
        authors = ", ".join([author.name for author in result.authors])
        published_date = result.published.strftime("%Y-%m-%d")
        url = result.entry_id
        pdf_url = result.pdf_url
        
        # Ajouter à la liste
        articles.append({
            "id": article_id,
            "title": title,
            "authors": authors,
            "published_date": published_date,
            "url": url,
            "pdf_url": pdf_url
        })
    
    # Créer un nouveau DataFrame
    new_df = pd.DataFrame(articles)
    
    # Si le fichier existe, charger et mettre à jour
    if os.path.exists(RESULTS_FILE):
        old_df = pd.read_csv(RESULTS_FILE)
        
        # Fusionner en évitant les doublons (basé sur l'ID)
        combined_df = pd.concat([old_df, new_df]).drop_duplicates(subset=["id"])
        
        # Trier par date (plus récent en premier)
        combined_df = combined_df.sort_values(by=["published_date"], ascending=False)
    else:
        combined_df = new_df.sort_values(by=["published_date"], ascending=False)
    
    # Sauvegarder
    combined_df.to_csv(RESULTS_FILE, index=False)
    print(f"Base de données mise à jour: {len(combined_df)} articles au total")
    
    return combined_df

def generate_readme(df):
    """Génère le fichier README avec un tableau des articles"""
    # En-tête du fichier
    header = f"""# Collection d'articles sur les Variétés Coisotropes

Dernière mise à jour: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Ce dépôt contient une collection d'articles scientifiques sur les variétés coisotropes et sujets connexes, collectés automatiquement depuis arXiv.

## Articles ({len(df)} au total)

| Date | Auteurs | Titre | Lien |
|------|---------|-------|------|
"""
    
    # Contenu du tableau
    rows = []
    for _, row in df.iterrows():
        article_id = row["id"]
        title = row["title"].replace("|", "\\|")  # Échapper les caractères pipe pour Markdown
        authors = row["authors"].replace("|", "\\|")
        date = row["published_date"]
        url = row["url"]
        
        # Créer une ligne de tableau Markdown
        row_str = f"| {date} | {authors} | {title} | [arXiv:{article_id}]({url}) |"
        rows.append(row_str)
    
    # Pied de page
    footer = """

## À propos

Ce tableau est généré automatiquement à l'aide d'un script Python qui interroge l'API arXiv. Le code source est disponible dans ce dépôt.

Pour suggérer des améliorations ou signaler des problèmes, veuillez ouvrir une issue.
"""
    
    # Combiner et écrire le fichier README
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(rows) + footer)
    
    print(f"Fichier README mis à jour: {README_FILE}")

def main():
    """Fonction principale"""
    # Récupérer les articles
    results = fetch_articles()
    
    # Mettre à jour la base de données
    df = update_database(results)
    
    # Générer le README
    generate_readme(df)

if __name__ == "__main__":
    main()
