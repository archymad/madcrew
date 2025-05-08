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
        # Contenu du script crew_exec.py
        script_content = f'''
# generated_crews/{kebab_case(project_title)}/crew_exec.py

import os
import sys
import datetime
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from crewai import Agent, Task, Crew, Process

# Charger les variables d'environnement depuis le fichier .env à la racine du projet
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
dotenv_path = os.path.join(root_dir, ".env")
load_dotenv(dotenv_path)

def exec_crew():
    """
    Exécute une crew pour le développement du projet "{project_title}".
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
    
    # Création du répertoire logs s'il n'existe pas
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Liste pour stocker les résultats des différentes itérations
    all_results = []
    
    # Initialisation du modèle LLM avec la clé API depuis les variables d'environnement
    llm = ChatAnthropic(
        model="claude-3-opus-20240229", 
        temperature=0.4,
        anthropic_api_key=os.environ["ANTHROPIC_API_KEY"]
    )
    
    while iteration_count < max_iterations and not approved:
        iteration_count += 1
        print(f"Démarrage de l'itération {{iteration_count}}/{{max_iterations}}")
        
        # Création des agents
        project_manager = Agent(
            role="Project Manager",
            goal="Superviser et coordonner l'ensemble du projet {project_title}",
            backstory="Un chef de projet expérimenté avec une expertise dans la gestion de projets complexes.",
            llm=llm,
            verbose=True
        )
        
        developer = Agent(
            role="Développeur",
            goal="Implémenter les fonctionnalités selon les spécifications du projet {project_title}",
            backstory="Un développeur expérimenté avec une expertise en architecture logicielle et développement web.",
            llm=llm,
            verbose=True
        )
        
        tester = Agent(
            role="Testeur",
            goal="Assurer la qualité et la fiabilité du projet {project_title}",
            backstory="Expert en assurance qualité qui cherche à garantir l'excellence des logiciels.",
            llm=llm,
            verbose=True
        )
        
        quality_controller = Agent(
            role="QualityController",
            goal="Évaluer la qualité globale du projet {project_title} et ses livrables",
            backstory="Un expert en contrôle qualité avec une expérience approfondie dans l'évaluation de projets similaires.",
            llm=llm,
            verbose=True
        )
        
        # Création des tâches de développement et de test
        dev_task = Task(
            description="Implémenter les fonctionnalités de base du projet {project_title}",
            expected_output="Code fonctionnel répondant aux exigences du projet",
            agent=developer
        )
        
        test_task = Task(
            description="Tester les fonctionnalités implémentées du projet {project_title}",
            expected_output="Rapport de test complet avec recommandations",
            agent=tester
        )
        
        try:
            # Exécuter les tâches de développement et de test
            if "{project_mode}" == "agile":
                # Mode agile : les agents collaborent directement
                dev_test_crew = Crew(
                    agents=[developer, tester],
                    tasks=[dev_task, test_task],
                    process=Process.agile,
                    verbose=True
                )
            else:
                # Mode hiérarchique : manager délègue et supervise
                dev_test_crew = Crew(
                    agents=[developer, tester],
                    tasks=[dev_task, test_task],
                    process=Process.sequential,  # Sequential pour éviter les problèmes de délégation
                    verbose=True
                )
            
            dev_test_results = dev_test_crew.kickoff()
            
            # Stocker les résultats
            all_results.append({{
                "iteration": iteration_count,
                "dev_results": str(dev_test_results),
                "tasks": [dev_task, test_task]
            }})
            
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
                f"Examiner les livrables de l'itération {{iteration_count}} du projet {project_title} et évaluer si le projet répond aux exigences. "
                f"S'il y a des problèmes majeurs, inclure le mot 'retry' dans votre réponse pour lancer une nouvelle itération.\\n\\n"
                f"Voici les résultats de l'itération actuelle :\\n{{str(dev_test_results)[:1000]}}..."
            )
            
            # Créer la tâche d'auto-évaluation
            review_task = Task(
                description=review_description,
                expected_output="Rapport d'évaluation avec décision finale: approuvé ou retry",
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
    generate_summary(all_results, iteration_count, [developer, tester, quality_controller], approved)
    
    return all_results

def generate_summary(results, iterations, agents, approved):
    """
    Génère un fichier summary.md avec un récapitulatif des résultats
    
    Args:
        results (list): Liste des résultats des itérations
        iterations (int): Nombre d'itérations effectuées
        agents (list): Liste des agents utilisés
        approved (bool): Indique si le projet a été approuvé
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open("summary.md", "w", encoding="utf-8") as f:
        f.write(f"# Résumé du projet {project_title}\\n\\n")
        f.write(f"Date: {{timestamp}}\\n\\n")
        f.write(f"## Informations générales\\n\\n")
        f.write(f"- Nombre d'itérations: {{iterations}}\\n")
        f.write(f"- Statut final: {{'Approuvé' if approved else 'Nécessite des améliorations'}}\\n\\n")
        
        f.write(f"## Agents utilisés\\n\\n")
        for agent in agents:
            f.write(f"### {{agent.role}}\\n")
            f.write(f"- Objectif: {{agent.goal}}\\n")
            f.write(f"- Expérience: {{agent.backstory}}\\n\\n")
        
        f.write(f"## Tâches accomplies par itération\\n\\n")
        
        for iteration_data in results:
            iteration_num = iteration_data.get("iteration", "?")
            tasks = iteration_data.get("tasks", [])
            
            f.write(f"### Itération {{iteration_num}}\\n\\n")
            
            for task in tasks:
                short_description = task.description
                f.write(f"#### {{short_description}}\\n")
                f.write(f"- Agent responsable: {{task.agent.role}}\\n")
                f.write(f"- Résultat attendu: {{task.expected_output}}\\n\\n")
            
            # Ajouter les résultats de développement
            dev_results = iteration_data.get("dev_results", "")
            if dev_results:
                f.write("#### Résultats de développement et tests:\\n\\n")
                f.write("```\\n")
                # Pas de limitation de taille, résultats complets
                f.write(dev_results + "\\n")
                f.write("```\\n\\n")
            
            # Ajouter les résultats d'auto-évaluation
            review_results = iteration_data.get("review_results", "")
            if review_results:
                f.write("#### Résultats de l'auto-évaluation:\\n\\n")
                f.write("```\\n")
                # Pas de limitation de taille, résultats complets
                f.write(review_results + "\\n")
                f.write("```\\n\\n")
        
        f.write(f"## Conclusion\\n\\n")
        if iterations == 1 and approved:
            f.write("Le projet a été approuvé dès la première itération, ce qui témoigne d'une excellente qualité des livrables.\\n")
        elif approved:
            f.write(f"Le projet a nécessité {{iterations}} itérations avant d'être approuvé. Des améliorations ont été apportées suite aux retours du contrôleur qualité.\\n")
        else:
            f.write(f"Le projet a atteint le nombre maximum d'itérations ({{iterations}}) sans être complètement approuvé. Des améliorations supplémentaires sont nécessaires.\\n")

if __name__ == "__main__":
    # Exécution directe pour les tests
    exec_crew()
'''
        
        # Remplacer le placeholder par le vrai mode du projet
        script_content = script_content.replace("{project_mode}", project_mode)
        
        # Écrire le fichier
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
        # Créer une nouvelle tâche de clarification
        clarification_task = Task(
            description=f"Clarifier les objectifs du projet intitulé '{project_title}'",
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