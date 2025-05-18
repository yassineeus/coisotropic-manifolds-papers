import arxiv
import pandas as pd
import datetime
import os
import yaml
from pathlib import Path
import re
import time
from tqdm import tqdm

# Configuration améliorée avec plus de mots-clés et termes pertinents
SEARCH_QUERIES = [
    'coisotropic manifold',
    '"coisotropic submanifold"',
    '"coisotropic structure"',
    '"coisotropic reduction"',
    '"coisotropic embedding"',
    '"coisotropic intersection"',
    'coisotropic AND "symplectic geometry"',
    'coisotropic AND "Poisson geometry"',
    'coisotropic AND "Dirac structure"',
    'coisotropic AND lagrangian',
    'coisotropic AND "moment map"'
]

# Catégories spécifiques en mathématiques pour limiter les résultats non pertinents
CATEGORIES = [
    'math.SG',  # Symplectic Geometry
    'math.DG',  # Differential Geometry
    'math.AG',  # Algebraic Geometry
    'math-ph',  # Mathematical Physics
    'math.GT',  # Geometric Topology
    'math.QA'   # Quantum Algebra
]

MAX_RESULTS_PER_QUERY = 200  # Nombre maximum d'articles par requête
RESULTS_FILE = "coisotropic_manifolds_database.csv"  # Fichier de stockage
README_FILE = "README.md"  # Fichier de présentation
CONFIG_FILE = "config.yaml"  # Fichier de configuration

def load_or_create_config():
    """Charge ou crée un fichier de configuration"""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        # Configuration par défaut
        config = {
            'last_update': None,
            'search_queries': SEARCH_QUERIES,
            'categories': CATEGORIES,
            'max_results_per_query': MAX_RESULTS_PER_QUERY,
            'exclude_terms': ['non-coisotropic', 'anti-coisotropic']  # Termes à exclure
        }
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
    
    return config

def save_config(config):
    """Sauvegarde la configuration"""
    with open(CONFIG_FILE, 'w') as f:
        yaml.dump(config, f)

def build_query(terms, categories, exclude_terms=None):
    """Construit une requête de recherche arXiv optimisée"""
    # Ajouter les catégories avec OU logique
    cat_query = " OR ".join([f"cat:{cat}" for cat in categories])
    
    # Ajouter les termes à exclure
    exclude_query = ""
    if exclude_terms and len(exclude_terms) > 0:
        exclude_query = " AND " + " AND ".join([f"NOT ({term})" for term in exclude_terms])
    
    # Requête finale
    query = f"({terms}) AND ({cat_query}){exclude_query}"
    return query

def fetch_articles(config):
    """Récupère les articles depuis arXiv avec plusieurs requêtes précises"""
    all_results = []
    
    # Créer un client avec une configuration personnalisée
    client = arxiv.Client(
        page_size=100,
        delay_seconds=3,
        num_retries=5
    )
    
    # Effectuer des recherches pour chaque requête
    for query_term in tqdm(config['search_queries'], desc="Recherche de requêtes"):
        full_query = build_query(query_term, config['categories'], config['exclude_terms'])
        print(f"Recherche avec la requête: {full_query}")
        
        # Configurer la recherche
        search = arxiv.Search(
            query=full_query,
            max_results=config['max_results_per_query'],
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )
        
        try:
            # Récupérer les articles pour cette requête
            results = list(client.results(search))
            print(f"  → {len(results)} articles trouvés")
            all_results.extend(results)
            
            # Pause pour éviter de surcharger l'API
            time.sleep(2)
        except Exception as e:
            print(f"Erreur lors de la recherche '{query_term}': {e}")
    
    # Éliminer les doublons en utilisant l'ID unique
    unique_results = {result.get_short_id(): result for result in all_results}
    final_results = list(unique_results.values())
    
    print(f"Nombre total d'articles uniques récupérés: {len(final_results)}")
    return final_results

def filter_by_relevance(results, config):
    """Filtre les résultats pour ne garder que les articles pertinents"""
    relevant_results = []
    
    # Expressions régulières pour les termes importants (insensible à la casse)
    key_patterns = [re.compile(r'\b' + re.escape(term.replace('"', '')) + r'\b', re.IGNORECASE) 
                    for term in config['search_queries']]
    
    for result in results:
        # Vérifier dans le titre et le résumé
        text_to_check = f"{result.title} {result.summary}"
        
        # Vérifier si l'article contient au moins un terme clé
        is_relevant = any(pattern.search(text_to_check) for pattern in key_patterns)
        
        if is_relevant:
            relevant_results.append(result)
    
    print(f"Après filtrage par pertinence: {len(relevant_results)} articles")
    return relevant_results

def extract_article_info(result):
    """Extrait les informations détaillées d'un article arXiv"""
    article_id = result.get_short_id()
    title = result.title
    authors = ", ".join([author.name for author in result.authors])
    published_date = result.published.strftime("%Y-%m-%d")
    updated_date = result.updated.strftime("%Y-%m-%d") if hasattr(result, 'updated') else published_date
    abstract = result.summary
    categories = ", ".join(result.categories) if hasattr(result, 'categories') else ""
    url = result.entry_id
    pdf_url = result.pdf_url
    
    return {
        "id": article_id,
        "title": title,
        "authors": authors,
        "published_date": published_date,
        "updated_date": updated_date,
        "abstract": abstract,
        "categories": categories,
        "url": url,
        "pdf_url": pdf_url
    }

def update_database(results):
    """Met à jour la base de données d'articles avec plus d'informations"""
    # Extraire les informations détaillées
    articles = [extract_article_info(result) for result in results]
    
    # Créer un nouveau DataFrame
    new_df = pd.DataFrame(articles)
    
    # Si le fichier existe, charger et mettre à jour
    if os.path.exists(RESULTS_FILE):
        try:
            old_df = pd.read_csv(RESULTS_FILE)
            
            # Fusionner en évitant les doublons (basé sur l'ID)
            combined_df = pd.concat([old_df, new_df]).drop_duplicates(subset=["id"])
            
            # Trier par date (plus récent en premier)
            combined_df = combined_df.sort_values(by=["published_date"], ascending=False)
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier existant: {e}")
            combined_df = new_df.sort_values(by=["published_date"], ascending=False)
    else:
        combined_df = new_df.sort_values(by=["published_date"], ascending=False)
    
    # Sauvegarder
    combined_df.to_csv(RESULTS_FILE, index=False)
    print(f"Base de données mise à jour: {len(combined_df)} articles au total")
    
    return combined_df

def generate_readme(df, config):
    """Génère le fichier README avec un tableau des articles et statistiques"""
    # En-tête du fichier
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"""# Collection d'articles sur les Variétés Coisotropes

Dernière mise à jour: {current_time}

Ce dépôt contient une collection d'articles scientifiques sur les variétés coisotropes et sujets connexes, collectés automatiquement depuis arXiv.

## Statistiques

- Nombre total d'articles: {len(df)}
- Termes de recherche: {', '.join([f'`{q}`' for q in config['search_queries']])}
- Catégories arXiv ciblées: {', '.join([f'`{c}`' for c in config['categories']])}

## Articles récents (10 derniers)

| Date | Auteurs | Titre | Catégories | Lien |
|------|---------|-------|------------|------|
"""
    
    # Ajouter les 10 articles les plus récents
    recent_rows = []
    for _, row in df.head(10).iterrows():
        article_id = row["id"]
        title = row["title"].replace("|", "\\|")  # Échapper les caractères pipe pour Markdown
        authors = row["authors"].replace("|", "\\|")
        date = row["published_date"]
        url = row["url"]
        categories = row.get("categories", "").replace("|", "\\|")
        
        # Créer une ligne de tableau Markdown
        row_str = f"| {date} | {authors} | {title} | {categories} | [arXiv:{article_id}]({url}) |"
        recent_rows.append(row_str)
    
    # Préparation pour la liste complète
    all_articles = f"""
## Liste complète des articles

| Date | Auteurs | Titre | Lien |
|------|---------|-------|------|
"""
    
    # Contenu du tableau complet
    all_rows = []
    for _, row in df.iterrows():
        article_id = row["id"]
        title = row["title"].replace("|", "\\|")
        authors = row["authors"].replace("|", "\\|")
        date = row["published_date"]
        url = row["url"]
        
        row_str = f"| {date} | {authors} | {title} | [arXiv:{article_id}]({url}) |"
        all_rows.append(row_str)
    
    # Pied de page
    footer = f"""

## À propos

Ce tableau est généré automatiquement à l'aide d'un script Python qui interroge l'API arXiv. Le code source est disponible dans ce dépôt.

Pour suggérer des améliorations ou signaler des problèmes, veuillez ouvrir une issue.

## Configuration

Le script utilise les paramètres suivants:
- Recherches: {', '.join(config['search_queries'])}
- Catégories: {', '.join(config['categories'])}
- Termes exclus: {', '.join(config['exclude_terms'])}
- Dernière exécution complète: {current_time}
"""
    
    # Combiner et écrire le fichier README
    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(recent_rows) + all_articles + "\n".join(all_rows) + footer)
    
    print(f"Fichier README mis à jour: {README_FILE}")

def main():
    """Fonction principale avec gestion des erreurs et rapport"""
    start_time = datetime.datetime.now()
    print(f"Démarrage de la collection d'articles à {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Charger ou créer la configuration
        config = load_or_create_config()
        
        # Récupérer les articles
        results = fetch_articles(config)
        
        # Filtrer par pertinence
        relevant_results = filter_by_relevance(results, config)
        
        # Mettre à jour la base de données
        df = update_database(relevant_results)
        
        # Générer le README
        generate_readme(df, config)
        
        # Mettre à jour la date de dernière exécution
        config['last_update'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_config(config)
        
        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds() / 60
        print(f"Traitement terminé en {duration:.2f} minutes")
        
    except Exception as e:
        print(f"Erreur lors de l'exécution: {e}")

if __name__ == "__main__":
    main()
