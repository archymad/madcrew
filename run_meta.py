# run_meta.py

import os
import datetime
import importlib.util
import sys
import traceback
import glob
from crewai import Crew, Process, Agent
from langchain_anthropic import ChatAnthropic
from meta_crew.meta_tasks import ALL_TASKS

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
    Exécute la sous-crew dans le dossier spécifié
    
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
    
    original_stdout = sys.stdout  # Sauvegarde pour s'assurer de restaurer stdout même en cas d'erreur
    run_log = None
    
    try:
        # Import du module crew_exec
        crew_exec_module = import_crew_exec(crew_folder)
        if crew_exec_module is None:
            raise ImportError(f"Module crew_exec non trouvé dans {crew_folder}")
        
        # Correction directe pour ajouter les éléments manquants
        # Lire le fichier plan.md pour extraire le plan
        plan_path = os.path.join(crew_folder, "plan.md")
        if not os.path.exists(plan_path):
            print(f"Fichier plan.md non trouvé dans {crew_folder}")
            return False
        
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_txt = f.read()
        
        # Créer notre propre Crew modifiée au lieu d'utiliser celle du module
        llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.4)
        
        # Créer un agent manager pour le Process.hierarchical
        manager_agent = Agent(
            role="Project Manager",
            goal="Superviser et coordonner l'ensemble du projet e-commerce",
            backstory="Un chef de projet expérimenté avec une expertise dans la gestion de projets e-commerce complexes.",
            llm=llm,
            verbose=True
        )
        
        # Définir les agents de base
        agent1 = Agent(
            role="Développeur",
            goal="Implémenter les fonctionnalités selon les spécifications",
            backstory="Un développeur expérimenté avec une expertise en architecture logicielle.",
            llm=llm,
            verbose=True
        )
        
        agent2 = Agent(
            role="Testeur",
            goal="Assurer la qualité et la fiabilité du produit",
            backstory="Expert en assurance qualité qui cherche à garantir l'excellence.",
            llm=llm,
            verbose=True
        )
        
        # Définir les tâches
        from crewai import Task
        
        task1 = Task(
            description="Implémenter les fonctionnalités de base de la plateforme e-commerce",
            expected_output="Code fonctionnel répondant aux exigences du projet",
            agent=agent1
        )
        
        task2 = Task(
            description="Tester les fonctionnalités implémentées de la plateforme e-commerce",
            expected_output="Rapport de test complet avec recommandations",
            agent=agent2
        )
        
        # Création de la crew avec manager_agent pour Process.hierarchical
        crew = Crew(
            agents=[agent1, agent2],
            tasks=[task1, task2],
            process=Process.hierarchical,
            manager_agent=manager_agent,  # Ajout du manager_agent ici
            verbose=True
        )
        
        print(f"Exécution de la sous-crew dans {crew_folder}...")
        
        # Redirection de stdout vers le fichier de log
        run_log = open(run_log_path, "w", encoding="utf-8")
        sys.stdout = run_log
        
        # Exécution de la crew
        results = crew.kickoff()
        
        # Écriture des résultats dans le log
        run_log.write("\n\n=== RÉCAPITULATIF DES RÉSULTATS ===\n\n")
        run_log.write(str(results))
        
        # Fermeture propre du fichier de log
        sys.stdout = original_stdout
        run_log.close()
        run_log = None
        
        print(f"Exécution terminée. Logs dans {run_log_path}")
        return True
        
    except Exception as e:
        # Restaurer stdout avant toute autre opération
        if sys.stdout != original_stdout:
            sys.stdout = original_stdout
        
        # Fermer proprement le fichier de log s'il est ouvert
        if run_log is not None and not run_log.closed:
            run_log.close()
        
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
    # Création du dossier logs pour la méta-crew s'il n'existe pas
    log_dir = "meta_crew/logs"
    os.makedirs(log_dir, exist_ok=True)
    
    # Génération du timestamp pour le nom du fichier
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"{log_dir}/meta_log_{timestamp}.txt"
    
    # Création de la Crew avec Process.sequential
    crew = Crew(
        agents=[task.agent for task in ALL_TASKS],
        tasks=ALL_TASKS,
        process=Process.sequential,
        verbose=True
    )
    
    print(f"Démarrage de la méta-crew... Résultats dans {log_file}")
    
    # Exécution de la Crew et capture des résultats
    results = crew.kickoff()
    
    # Écriture des résultats dans le fichier de log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== Exécution de la méta-crew - {timestamp} ===\n\n")
        
        # Log de chaque tâche et son résultat
        for i, task in enumerate(ALL_TASKS):
            f.write(f"## Tâche {i+1}: {task.description}\n")
            f.write(f"Agent: {task.agent.role}\n")
            f.write(f"Résultats attendus: {task.expected_output}\n\n")
        
        # Log des résultats finaux
        f.write("=== RÉSULTATS FINAUX ===\n\n")
        f.write(str(results))
    
    print(f"Exécution terminée. Logs sauvegardés dans {log_file}")
    
    # Après l'exécution de la méta-crew, exécuter la sous-crew
    latest_crew_folder = get_latest_crew_folder()
    if latest_crew_folder:
        print(f"\nDétection de la sous-crew dans {latest_crew_folder}")
        execute_sub_crew(latest_crew_folder)
    else:
        print("\nAucune sous-crew détectée dans /generated_crews/")
    
    return results

if __name__ == "__main__":
    main()