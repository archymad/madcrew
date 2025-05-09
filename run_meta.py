# run_meta.py

import os
import datetime
import importlib.util
import sys
import traceback
import json
import re
from crewai import Crew, Process, Task, Agent
from langchain_anthropic import ChatAnthropic
from meta_crew.meta_tasks import ALL_TASKS
from meta_crew import meta_agents

def kebab_case(s):
    """
    Convertit une chaîne en format kebab-case.
    
    Args:
        s (str): Chaîne à convertir
    
    Returns:
        str: Chaîne en format kebab-case
    """
    # Convertir en minuscules
    s = s.lower()
    # Remplacer les caractères non alphanumériques par des tirets
    s = re.sub(r'[^a-z0-9]+', '-', s)
    # Supprimer les tirets en début et fin de chaîne
    s = s.strip('-')
    return s

def load_project_config():
    """
    Charge la configuration du projet depuis le fichier JSON.
    
    Returns:
        dict: Configuration du projet ou dictionnaire vide si le fichier n'existe pas.
    """
    config_path = ".madcrew/current_project.json"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # En cas d'absence du fichier, regarder la variable d'environnement
    if "MADCREW_CONFIG_PATH" in os.environ:
        env_config_path = os.environ["MADCREW_CONFIG_PATH"]
        if os.path.exists(env_config_path):
            with open(env_config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    
    return {}

def get_latest_crew_folder():
    """
    Trouve le dossier créé le plus récemment dans /generated_crews/
    
    Returns:
        str: Chemin vers le dossier le plus récent ou None si aucun n'est trouvé
    """
    generated_crews_path = "generated_crews"
    
    # S'assurer que le dossier existe
    if not os.path.exists(generated_crews_path):
        return None
    
    # Obtenir tous les sous-dossiers de generated_crews
    subfolders = [f for f in os.listdir(generated_crews_path) 
                if os.path.isdir(os.path.join(generated_crews_path, f)) and f != '.gitkeep']
    
    if not subfolders:
        return None
    
    # Trouver le dossier avec la date de modification la plus récente
    latest_subfolder = max(subfolders, 
                        key=lambda f: os.path.getmtime(os.path.join(generated_crews_path, f)))
    
    return os.path.join(generated_crews_path, latest_subfolder)

def create_crew_exec_script(project_folder, project_title, project_mode="hierarchical"):
    """
    Crée un nouveau fichier crew_exec.py adapté au projet spécifique.
    
    Args:
        project_folder (str): Chemin vers le dossier du projet
        project_title (str): Titre du projet
        project_mode (str): Mode de fonctionnement (hierarchical ou agile)
    
    Returns:
        bool: True si la création est réussie, False sinon
    """
    try:
        # Chemin vers le modèle de fichier crew_exec.py
        template_path = os.path.join("meta_crew", "templates", "crew_exec_template.py")
        
        # Si le template existe, l'utiliser, sinon utiliser le contenu par défaut
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as f:
                script_content = f.read()
        else:
            # Charger le contenu depuis le code intégré dans ce script
            # C'est une version simplifiée, idéalement vous auriez un template complet
            script_content = '''
# generated_crews/{kebab_case(project_title)}/crew_exec.py

import os
import sys
import datetime
import json
import re
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from crewai import Agent, Task, Crew, Process

# Charger les variables d'environnement depuis le fichier .env à la racine du projet
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)

class ArtifactManager:
    """Gestionnaire d'artefacts pour stocker les codes et documents complets."""
    
    def __init__(self, project_name):
        """Initialise le gestionnaire d'artefacts avec un nom de projet."""
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.artifacts_dir = os.path.join(self.project_dir, "artifacts")
        self.code_dir = os.path.join(self.artifacts_dir, "code")
        self.docs_dir = os.path.join(self.artifacts_dir, "docs")
        self.tests_dir = os.path.join(self.artifacts_dir, "tests")
        
        # Création des répertoires nécessaires
        for directory in [self.artifacts_dir, self.code_dir, self.docs_dir, self.tests_dir]:
            os.makedirs(directory, exist_ok=True)
        
        self.project_name = project_name
        
    def save_code(self, filename, content, language="python"):
        """Sauvegarde un fichier de code complet."""
        filepath = os.path.join(self.code_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Code sauvegardé dans {filepath}")
        return filepath
        
    def save_document(self, filename, content):
        """Sauvegarde un document."""
        filepath = os.path.join(self.docs_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📄 Document sauvegardé dans {filepath}")
        return filepath
        
    def save_test(self, filename, content):
        """Sauvegarde un fichier de test."""
        filepath = os.path.join(self.tests_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"🧪 Test sauvegardé dans {filepath}")
        return filepath
        
    def list_artifacts(self):
        """Liste tous les artefacts créés."""
        artifacts = []
        for root, _, files in os.walk(self.artifacts_dir):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), self.artifacts_dir)
                artifacts.append(rel_path)
        return artifacts

def extract_code_from_response(response_text):
    """
    Extrait le code source des réponses des agents.
    
    Args:
        response_text (str): Texte complet de la réponse
    
    Returns:
        dict: Dictionnaire des fichiers avec leur code source
    """
    code_files = {}
    
    # Recherche de blocs de code avec indication de langage
    code_blocks = re.finditer(r'```(?:python|javascript|java|html|css|c\+\+|php|)?\s*(.*?)```', response_text, re.DOTALL)
    
    for i, match in enumerate(code_blocks):
        code = match.group(1).strip()
        
        # Rechercher un nom de fichier potentiel avant le bloc de code
        file_name_match = re.search(r'(?:fichier|file):\s*[\'"]?([a-zA-Z0-9_\-\.]+\.[a-zA-Z0-9]+)[\'"]?', 
                                   response_text[:match.start()], re.IGNORECASE)
        
        if file_name_match:
            filename = file_name_match.group(1)
        else:
            # Essayer de déduire le nom du fichier à partir du contenu du code
            if "class Character" in code and ".py" not in code:
                filename = "character.py"
            elif "def generate" in code and ".py" not in code:
                filename = "generator.py"
            elif "import React" in code:
                filename = "app.jsx"
            elif "<html" in code:
                filename = "index.html"
            elif "body {" in code:
                filename = "style.css"
            else:
                filename = f"code_block_{i+1}.py"
        
        code_files[filename] = code
    
    return code_files

def extract_test_report(response_text):
    """
    Extrait le rapport de test des réponses des agents.
    
    Args:
        response_text (str): Texte complet de la réponse
    
    Returns:
        str: Rapport de test formaté en markdown
    """
    # Recherche d'un rapport de test
    test_report_match = re.search(r'Rapport de test.*?(?=```|$)', response_text, re.DOTALL | re.IGNORECASE)
    
    if test_report_match:
        return f"# Rapport de test\\n\\n{test_report_match.group(0).strip()}"
    
    return None

def exec_crew():
    """
    Exécute une crew pour le développement du projet {project_title}.
    Cette fonction inclut une boucle d'auto-évaluation qui permet jusqu'à 2 itérations.
    
    Returns:
        dict: Résultats de l'exécution
    """
    # Vérifier que la clé API est disponible
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("Erreur: ANTHROPIC_API_KEY n'est pas définie dans les variables d'environnement.")
        print(f"Chemin du .env recherché: {{dotenv_path}}")
        sys.exit(1)
    
    # Initialisation du compteur d'itérations
    iteration_count = 0
    max_iterations = 2
    approved = False
    
    # Nom du projet
    project_name = "{project_title}"
    
    # Création du gestionnaire d'artefacts
    artifact_manager = ArtifactManager(project_name)
    
    # Création du répertoire logs s'il n'existe pas
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Liste pour stocker les résultats des différentes itérations
    all_results = []
    
    # Initialisation du modèle LLM avec la clé API depuis les variables d'environnement
    llm = ChatAnthropic(
        model="claude-3-opus-20240229", 
        temperature=0.2,
        max_tokens_to_sample=4000,
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"]
    )
    
    while iteration_count < max_iterations and not approved:
        iteration_count += 1
        print(f"Démarrage de l'itération {{iteration_count}}/{{max_iterations}}")
        
        # Création des agents avec des instructions améliorées
        project_manager = Agent(
            role="Project Manager",
            goal="Superviser et coordonner l'ensemble du projet {project_title}",
            backstory="Un chef de projet expérimenté avec une expertise dans la gestion de projets complexes.",
            llm=llm,
            verbose=True
        )
        
        developer = Agent(
            role="Développeur",
            goal="Implémenter des fichiers complets et fonctionnels pour le projet {project_title}",
            backstory=(
                "Un développeur expérimenté avec une expertise en architecture logicielle. "
                "Votre mission est de produire du code complet, fonctionnel et bien documenté. "
                "Pour chaque fichier que vous créez, assurez-vous qu'il est complet du début à la fin, "
                "incluant toutes les importations, classes, méthodes et la documentation nécessaire."
            ),
            llm=llm,
            verbose=True
        )
        
        tester = Agent(
            role="Testeur",
            goal="Assurer la qualité et la fiabilité du projet {project_title}",
            backstory=(
                "Expert en assurance qualité qui cherche à garantir l'excellence des logiciels. "
                "Votre mission est de tester de manière exhaustive toutes les fonctionnalités, "
                "de documenter les cas de test, les résultats et les recommandations d'amélioration "
                "dans un format clair et complet. Incluez des exemples concrets avec les entrées et sorties attendues."
            ),
            llm=llm,
            verbose=True
        )
        
        quality_controller = Agent(
            role="QualityController",
            goal="Évaluer la qualité globale du projet {project_title} et ses livrables",
            backstory=(
                "Un expert en contrôle qualité avec une expérience approfondie dans l'évaluation de projets similaires. "
                "Votre mission est d'examiner de manière critique tous les livrables, d'identifier les problèmes, "
                "les non-conformités et de proposer des améliorations concrètes."
            ),
            llm=llm,
            verbose=True
        )
        
        # Instructions pour le développeur afin de créer des fichiers complets
        dev_instructions = (
            f"Implémentez les fonctionnalités de base du projet {project_title}. "
            "Il est CRUCIAL que vous fournissiez du code COMPLET, du début à la fin, "
            "sans aucune troncature ou section manquante. Votre réponse doit inclure :\\n\\n"
            "1. Une analyse des besoins et une description de l'architecture choisie\\n"
            "2. Le code source COMPLET pour CHAQUE fichier nécessaire, en précisant clairement "
            "le nom de chaque fichier avant son contenu\\n"
            "3. Une explication de l'implémentation et des instructions d'utilisation\\n\\n"
            "IMPORTANT : Assurez-vous que chaque fichier de code contient toutes les importations, "
            "toutes les définitions de classes/fonctions, et est prêt à être exécuté sans modification. "
            "Ne tronquez JAMAIS le code avec des commentaires comme '# reste du code...' "
            "ou des ellipses '...'."
        )
        
        # Instructions pour le testeur afin de créer des rapports de test complets
        test_instructions = (
            f"Testez les fonctionnalités implémentées du projet {project_title}. "
            "Il est CRUCIAL que vous fournissiez un rapport de test COMPLET et DÉTAILLÉ. "
            "Votre réponse doit inclure :\\n\\n"
            "1. Une description détaillée de la méthodologie de test\\n"
            "2. Des cas de test spécifiques avec entrées et sorties attendues\\n"
            "3. Les résultats obtenus pour CHAQUE test, avec des exemples concrets\\n"
            "4. Une analyse des performances et des limites identifiées\\n"
            "5. Des recommandations d'amélioration spécifiques\\n\\n"
            "IMPORTANT : Incluez dans votre rapport au moins 3-5 exemples complets "
            "de personnages générés avec toutes leurs caractéristiques."
        )
        
        # Création des tâches de développement et de test avec les instructions améliorées
        dev_task = Task(
            description=dev_instructions,
            expected_output="Code source complet et fonctionnel pour tous les fichiers du projet",
            agent=developer
        )
        
        test_task = Task(
            description=test_instructions,
            expected_output="Rapport de test complet avec exemples et recommandations",
            agent=tester
        )
        
        try:
            # Exécuter les tâches de développement et de test
            dev_test_crew = Crew(
                agents=[developer, tester],
                tasks=[dev_task, test_task],
                process=Process.{project_mode},
                verbose=True
            )
            
            dev_test_results = dev_test_crew.kickoff()
            
            # Stocker les résultats
            all_results.append({{
                "iteration": iteration_count,
                "dev_results": str(dev_test_results),
                "tasks": [dev_task, test_task]
            }})
            
            # Extraction et sauvegarde du code depuis les résultats
            code_results = extract_code_from_response(str(dev_test_results))
            for filename, code in code_results.items():
                artifact_manager.save_code(filename, code)
            
            # Extraction et sauvegarde des résultats de test
            test_report = extract_test_report(str(dev_test_results))
            if test_report:
                artifact_manager.save_document("test_report.md", test_report)
            
            # Écrire les résultats dans un fichier pour référence
            with open(os.path.join(logs_dir, f"iteration_{{iteration_count}}_results.txt"), "w", encoding="utf-8") as f:
                f.write(str(dev_test_results))
            
            # Si c'est la dernière itération, on n'a pas besoin d'évaluation
            if iteration_count >= max_iterations:
                # Si c'est la dernière itération, on considère que c'est approuvé
                approved = True
                continue
            
            # Préparer la description de la tâche d'auto-évaluation avec les résultats précédents
            review_description = (
                f"Examiner les livrables de l'itération {{iteration_count}} du projet {project_title} "
                f"et évaluer si le projet répond aux exigences. Votre rapport doit être COMPLET et DÉTAILLÉ. "
                f"Analysez la qualité du code, la couverture des tests et la fonctionnalité globale. "
                f"S'il y a des problèmes majeurs, incluez le mot 'retry' dans votre réponse. "
                f"Si le projet est approuvé, expliquez clairement pourquoi.\\n\\n"
                f"Voici les artefacts produits lors de cette itération :\\n"
                f"{{json.dumps(artifact_manager.list_artifacts(), indent=2)}}\\n\\n"
                f"Voici un aperçu des résultats de l'itération actuelle :\\n"
                f"{{str(dev_test_results)[:2000]}}..."
            )
            
            # Créer la tâche d'auto-évaluation
            review_task = Task(
                description=review_description,
                expected_output="Rapport d'évaluation détaillé avec décision finale: approuvé ou retry",
                agent=quality_controller
            )
            
            # Créer une crew séparée pour l'auto-évaluation
            review_crew = Crew(
                agents=[quality_controller],
                tasks=[review_task],
                process=Process.sequential,
                verbose=True
            )
            
            try:
                # Exécuter l'auto-évaluation
                review_results = review_crew.kickoff()
                
                # Stocker les résultats
                all_results[-1]["review_results"] = str(review_results)
                all_results[-1]["tasks"].append(review_task)
                
                # Sauvegarde du rapport d'évaluation
                quality_report = str(review_results)
                artifact_manager.save_document(f"quality_report_iteration_{{iteration_count}}.md", quality_report)
                
                # Écrire les résultats dans un fichier pour référence
                with open(os.path.join(logs_dir, f"iteration_{{iteration_count}}_review.txt"), "w", encoding="utf-8") as f:
                    f.write(str(review_results))
                
                # Analyser le résultat pour décider si une autre itération est nécessaire
                review_result_str = str(review_results)
                if "retry" not in review_result_str.lower():
                    approved = True
                    print(f"Auto-évaluation approuvée à l'itération {{iteration_count}}")
                else:
                    print(f"Auto-évaluation recommande une nouvelle itération")
                    
                    # Si c'est la dernière itération, indiquer que la limite est atteinte
                    if iteration_count >= max_iterations:
                        print(f"Nombre maximum d'itérations atteint ({{max_iterations}})")
                
            except Exception as review_error:
                print(f"Erreur lors de l'exécution de la tâche d'auto-évaluation: {{str(review_error)}}")
                # Enregistrer l'erreur dans un fichier de log
                error_log_path = os.path.join(logs_dir, "error.log")
                with open(error_log_path, "a", encoding="utf-8") as error_log:
                    error_log.write(f"=== ERREUR D'EXÉCUTION DE L'AUTO-ÉVALUATION - {{datetime.datetime.now()}} ===\\n")
                    error_log.write(f"Itération: {{iteration_count}}\\n")
                    error_log.write(f"Exception: {{str(review_error)}}\\n\\n")
                
                # Si c'est la dernière itération, sortir de la boucle
                if iteration_count >= max_iterations:
                    print(f"Nombre maximum d'itérations atteint ({{max_iterations}})")
                    
        except Exception as e:
            print(f"Erreur lors de l'exécution de la crew: {{str(e)}}")
            # Enregistrer l'erreur dans un fichier de log
            error_log_path = os.path.join(logs_dir, "error.log")
            with open(error_log_path, "a", encoding="utf-8") as error_log:
                error_log.write(f"=== ERREUR D'EXÉCUTION - {{datetime.datetime.now()}} ===\\n")
                error_log.write(f"Itération: {{iteration_count}}\\n")
                error_log.write(f"Exception: {{str(e)}}\\n\\n")
            
            # Si c'est la dernière itération, sortir de la boucle
            if iteration_count >= max_iterations:
                print(f"Nombre maximum d'itérations atteint ({{max_iterations}})")
    
    # Générer le fichier summary.md
    generate_summary(all_results, artifact_manager, iteration_count, [developer, tester, quality_controller], approved)
    
    return all_results

def generate_summary(results, artifact_manager, iterations, agents, approved):
    """
    Génère un fichier summary.md avec un récapitulatif des résultats
    
    Args:
        results (list): Liste des résultats des itérations
        artifact_manager (ArtifactManager): Gestionnaire d'artefacts
        iterations (int): Nombre d'itérations effectuées
        agents (list): Liste des agents utilisés
        approved (bool): Indique si le projet a été approuvé
    """
    project_name = artifact_manager.project_name
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Liste des artefacts générés
    artifacts = artifact_manager.list_artifacts()
    
    with open(os.path.join(artifact_manager.project_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(f"# Résumé du projet {{project_name}}\\n\\n")
        f.write(f"Date: {{timestamp}}\\n\\n")
        f.write(f"## Informations générales\\n\\n")
        f.write(f"- Nombre d'itérations: {{iterations}}\\n")
        f.write(f"- Statut final: {{'Approuvé' if approved else 'Nécessite des améliorations'}}\\n\\n")
        
        f.write(f"## Agents utilisés\\n\\n")
        for agent in agents:
            f.write(f"### {{agent.role}}\\n")
            f.write(f"- Objectif: {{agent.goal}}\\n")
            f.write(f"- Expérience: {{agent.backstory}}\\n\\n")
        
        f.write(f"## Artefacts produits\\n\\n")
        f.write("| Fichier | Type |\\n")
        f.write("| ------ | ---- |\\n")
        for artifact in artifacts:
            artifact_type = "Code" if artifact.startswith("code/") else "Document" if artifact.startswith("docs/") else "Test"
            f.write(f"| {{artifact}} | {{artifact_type}} |\\n")
        f.write("\\n\\n")
        
        f.write(f"## Tâches accomplies par itération\\n\\n")
        
        for iteration_data in results:
            iteration_num = iteration_data.get("iteration", "?")
            tasks = iteration_data.get("tasks", [])
            
            f.write(f"### Itération {{iteration_num}}\\n\\n")
            
            for task in tasks:
                short_description = task.description.split('\\n')[0]
                f.write(f"#### {{short_description}}\\n")
                f.write(f"- Agent responsable: {{task.agent.role}}\\n")
                f.write(f"- Résultat attendu: {{task.expected_output}}\\n\\n")
        
        f.write(f"## Conclusion\\n\\n")
        if iterations == 1 and approved:
            f.write("Le projet a été approuvé dès la première itération, ce qui témoigne d'une excellente qualité des livrables.\\n")
        elif approved:
            f.write(f"Le projet a nécessité {{iterations}} itérations avant d'être approuvé. Des améliorations ont été apportées suite aux retours du contrôleur qualité.\\n")
        else:
            f.write(f"Le projet a atteint le nombre maximum d'itérations ({{iterations}}) sans être complètement approuvé. Des améliorations supplémentaires sont nécessaires.\\n")
        
        f.write("\\n## Instructions d'exécution\\n\\n")
        
        # Détecter automatiquement le type de projet et générer des instructions d'exécution
        python_files = [f for f in artifacts if f.endswith('.py') and f.startswith('code/')]
        js_files = [f for f in artifacts if f.endswith('.js') and f.startswith('code/')]
        html_files = [f for f in artifacts if f.endswith('.html') and f.startswith('code/')]
        
        if python_files:
            main_file = next((f for f in python_files if 'main' in f), python_files[0])
            rel_path = os.path.join('artifacts', main_file)
            f.write(f"Pour exécuter ce projet Python :\\n\\n")
            f.write(f"```bash\\n")
            f.write(f"cd {{project_name}}\\n")
            f.write(f"python {{rel_path}}\\n")
            f.write(f"```\\n\\n")
        
        if js_files and html_files:
            f.write(f"Pour exécuter ce projet web :\\n\\n")
            f.write(f"Ouvrez le fichier `artifacts/{{next(f for f in html_files)}}` dans votre navigateur.\\n\\n")

if __name__ == "__main__":
    # Exécution directe pour les tests
    exec_crew()
'''
        
        # Remplacer les placeholders
        script_content = script_content.replace("{project_title}", project_title)
        script_content = script_content.replace("{project_mode}", project_mode)
        script_content = script_content.replace("{kebab_case(project_title)}", kebab_case(project_title))
        
        # Créer les répertoires
        artifacts_dir = os.path.join(project_folder, "artifacts")
        os.makedirs(os.path.join(artifacts_dir, "code"), exist_ok=True)
        os.makedirs(os.path.join(artifacts_dir, "docs"), exist_ok=True)
        os.makedirs(os.path.join(artifacts_dir, "tests"), exist_ok=True)
        
        # Écrire le fichier crew_exec.py
        crew_exec_path = os.path.join(project_folder, "crew_exec.py")
        with open(crew_exec_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        print(f"Script crew_exec.py créé dans {crew_exec_path}")
        return True
        
    except Exception as e:
        print(f"Erreur lors de la création du script crew_exec.py: {str(e)}")
        return False

def create_project_directory(project_title, plan_text):
    """
    Crée un nouveau dossier de projet dans generated_crews/ et génère les fichiers nécessaires.
    
    Args:
        project_title (str): Titre du projet
        plan_text (str): Contenu du plan de projet
    
    Returns:
        str: Chemin vers le dossier créé ou None en cas d'échec
    """
    # Convertir le titre en kebab-case
    project_slug = kebab_case(project_title)
    
    # Chemin du dossier du projet
    project_dir = os.path.join("generated_crews", project_slug)
    
    try:
        # Créer le dossier du projet
        os.makedirs(project_dir, exist_ok=True)
        
        # Créer le dossier logs
        os.makedirs(os.path.join(project_dir, "logs"), exist_ok=True)
        
        # Créer le fichier plan.md
        with open(os.path.join(project_dir, "plan.md"), "w", encoding="utf-8") as f:
            f.write(plan_text)
        
        # Récupérer le mode depuis la configuration
        project_config = load_project_config()
        project_mode = project_config.get("structure", "hierarchical")
        
        # Créer le script crew_exec.py adapté au projet
        create_crew_exec_script(project_dir, project_title, project_mode)
        
        print(f"Dossier de projet créé: {project_dir}")
        return project_dir
        
    except Exception as e:
        print(f"Erreur lors de la création du dossier de projet: {str(e)}")
        return None

def import_crew_exec(crew_folder):
    """
    Importe dynamiquement le module crew_exec.py du dossier de crew spécifié
    
    Args:
        crew_folder (str): Chemin vers le dossier de la crew
    
    Returns:
        module: Module crew_exec importé ou None en cas d'échec
    """
    crew_exec_path = os.path.join(crew_folder, "crew_exec.py")
    
    if not os.path.exists(crew_exec_path):
        print(f"Fichier crew_exec.py non trouvé dans {crew_folder}")
        return None
    
    try:
        # Création d'un nom de module unique basé sur le chemin
        module_name = f"crew_exec_{os.path.basename(crew_folder)}"
        
        # Préparation de la spécification du module
        spec = importlib.util.spec_from_file_location(module_name, crew_exec_path)
        if spec is None:
            print(f"Impossible de charger la spécification du module depuis {crew_exec_path}")
            return None
        
        # Création du module
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        # Exécution du module
        spec.loader.exec_module(module)
        
        return module
    except Exception as e:
        print(f"Erreur lors de l'importation du module crew_exec: {str(e)}")
        return None

def execute_sub_crew(crew_folder):
    """
    Exécute la sous-crew dans le dossier spécifié, avec affichage en temps réel
    
    Args:
        crew_folder (str): Chemin vers le dossier de la crew
    
    Returns:
        bool: True si l'exécution est réussie, False sinon
    """
    if crew_folder is None:
        print("Aucun dossier de crew trouvé dans generated_crews/")
        return False
    
    # Création des dossiers de logs s'ils n'existent pas
    logs_folder = os.path.join(crew_folder, "logs")
    os.makedirs(logs_folder, exist_ok=True)
    
    # Chemins des fichiers de log
    run_log_path = os.path.join(logs_folder, "run.log")
    error_log_path = os.path.join(logs_folder, "error.log")
    
    try:
        # Import du module crew_exec
        crew_exec_module = import_crew_exec(crew_folder)
        if crew_exec_module is None:
            raise ImportError(f"Module crew_exec non trouvé dans {crew_folder}")
        
        print(f"Exécution de la sous-crew dans {crew_folder}...")
        print("=" * 80)
        
        # Créer une class Tee pour dupliquer la sortie vers la console et le fichier
        class Tee:
            def __init__(self, file_path):
                self.file = open(file_path, "w", encoding="utf-8")
                self.stdout = sys.stdout
                
            def write(self, data):
                self.file.write(data)
                self.stdout.write(data)
                
            def flush(self):
                self.file.flush()
                self.stdout.flush()
                
            def close(self):
                if self.file:
                    self.file.close()
        
        # Utiliser Tee pour dupliquer la sortie
        tee_output = Tee(run_log_path)
        sys.stdout = tee_output
        
        try:
            # Exécution de la fonction exec_crew
            results = crew_exec_module.exec_crew()
            
            # Écriture des résultats dans le log
            sys.stdout.write("\n\n=== RÉCAPITULATIF DES RÉSULTATS ===\n\n")
            sys.stdout.write(str(results))
        finally:
            # Restaurer sys.stdout et fermer le fichier de log
            sys.stdout = tee_output.stdout
            tee_output.close()
        
        print("=" * 80)
        print(f"Exécution terminée. Logs enregistrés dans {run_log_path}")
        return True
        
    except Exception as e:
        # Journalisation de l'erreur
        with open(error_log_path, "w", encoding="utf-8") as error_log:
            error_log.write(f"=== ERREUR D'EXÉCUTION DE LA SOUS-CREW - {datetime.datetime.now()} ===\n\n")
            error_log.write(f"Exception: {str(e)}\n\n")
            error_log.write("Traceback:\n")
            error_log.write(traceback.format_exc())
        
        print(f"Erreur lors de l'exécution de la sous-crew: {str(e)}")
        print(f"Détails de l'erreur enregistrés dans {error_log_path}")
        return False

def main():
    # Charger la configuration du projet
    project = load_project_config()
    project_title = project.get("project_title", "Projet sans titre")
    
    print(f"Traitement du projet: '{project_title}'")
    
    # Modifier dynamiquement les objectifs des agents
    meta_agents.project_manager.goal = f"Superviser le projet intitulé : '{project_title}'"
    meta_agents.strategic_planner.goal = f"Analyser et planifier précisément le projet '{project_title}'"
    meta_agents.team_architect.goal = f"Concevoir l'équipe idéale d'agents pour réaliser le projet '{project_title}'"
    meta_agents.quality_controller.goal = f"Valider chaque livrable produit dans le cadre du projet '{project_title}'"
    
    # Mettre à jour les paramètres du modèle LLM pour éviter les troncatures
    meta_agents.llm = ChatAnthropic(
        model="claude-3-opus-20240229", 
        temperature=0.2,
        max_tokens_to_sample=100000,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    # Création du dossier logs pour la méta-crew s'il n'existe pas
    log_dir = "meta_crew/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Génération du timestamp pour le nom du fichier
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/meta_log_{timestamp}.txt"
    
    # Ajouter une tâche de clarification si possible
    tasks = ALL_TASKS.copy()
    
    # Tentative d'ajout d'une tâche de clarification en première position
    try:
        # Créer une nouvelle tâche de clarification avec des instructions améliorées
        clarification_task = Task(
            description=(
                f"Clarifier les objectifs du projet intitulé '{project_title}'. "
                f"Fournissez une description détaillée des fonctionnalités, besoins et contraintes. "
                f"Ne pas tronquer vos réponses et être aussi exhaustif que possible. "
                f"Structurez votre réponse clairement avec des sections et sous-sections. "
                f"Soyez particulièrement attentif aux besoins fonctionnels et non-fonctionnels."
            ),
            expected_output=f"Document détaillant les objectifs, contraintes et priorités du projet '{project_title}'",
            agent=meta_agents.strategic_planner
        )
        
        # Ajouter au début de la liste des tâches
        tasks.insert(0, clarification_task)
        print(f"Tâche de clarification ajoutée pour le projet '{project_title}'")
    except Exception as e:
        print(f"Note: La tâche de clarification n'a pas pu être ajoutée: {str(e)}")
    
    # Création de la Crew avec Process.sequential
    crew = Crew(
        agents=[task.agent for task in tasks],
        tasks=tasks,
        process=Process.sequential,
        verbose=True
    )
    
    print(f"Démarrage de la méta-crew... Résultats dans {log_file}")
    
    # Exécution de la Crew et capture des résultats
    crew_results = crew.kickoff()
    
    # Écriture des résultats dans le fichier de log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== Exécution de la méta-crew pour le projet '{project_title}' - {timestamp} ===\n\n")
        
        # Log de chaque tâche et son résultat
        for i, task in enumerate(tasks):
            f.write(f"## Tâche {i+1}: {task.description}\n")
            f.write(f"Agent: {task.agent.role}\n")
            f.write(f"Résultats attendus: {task.expected_output}\n\n")
        
        # Log des résultats finaux
        f.write("=== RÉSULTATS FINAUX ===\n\n")
        f.write(str(crew_results))
    
    print(f"Exécution terminée. Logs sauvegardés dans {log_file}")
    
    # Extraire les résultats des tâches exécutées
    task_results = {}
    
    # Tenter d'extraire les résultats au format dictionnaire
    if hasattr(crew_results, "values"):
        task_dict = crew_results.values()
        for task_id, task_result in task_dict.items():
            # Trouver la tâche correspondante
            for task in tasks:
                if str(getattr(task, "id", "")) == str(task_id) or task.description == task_id:
                    task_results[task.description] = task_result
                    break
    
    # Si l'extraction échoue, essayer différentes approches
    if not task_results:
        # Convertir les résultats en chaîne et extraire manuellement
        results_str = str(crew_results)
        
        # Créer un plan de secours
        plan_text = "# Plan détaillé du projet\n\n"
        plan_text += f"## Plan pour le projet '{project_title}'\n\n"
        plan_text += results_str
        
        # Essayer d'identifier les sections par tâche
        for task in tasks:
            if task.agent == meta_agents.strategic_planner:
                plan_text += f"\n\n## {task.description}\n\n"
                if hasattr(crew_results, "get"):
                    task_output = crew_results.get(task.description)
                    if task_output:
                        plan_text += task_output
    else:
        # Créer le plan à partir des résultats extraits
        plan_text = "# Plan détaillé du projet\n\n"
        
        # Chercher d'abord les résultats du Strategic Planner
        for task in tasks:
            if task.agent == meta_agents.strategic_planner and task.description in task_results:
                plan_text += f"## {task.description}\n\n"
                plan_text += task_results[task.description]
                plan_text += "\n\n"
    
    # Créer le dossier du projet avec le plan généré
    project_dir = create_project_directory(project_title, plan_text)
    
    if project_dir:
        print(f"Le projet '{project_title}' a été généré avec succès!")
        print(f"Vous pouvez trouver les résultats dans 'generated_crews/{kebab_case(project_title)}'")
        
        # Exécuter la sous-crew
        execute_sub_crew(project_dir)
    else:
        print(f"Erreur lors de la génération du projet '{project_title}'")
    
    return crew_results

if __name__ == "__main__":
    main()