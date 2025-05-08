# create_crew.py
import os
import re
from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic
import datetime

def kebab_case(s):
    """
    Convertit une chaîne en format kebab-case.
    
    Args:
        s (str): Chaîne à convertir
    
    Returns:
        str: Chaîne en format kebab-case
    """
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s

def create_crew(plan_txt, crew_spec_dict):
    """
    Crée une structure de crew personnalisée basée sur le plan et les spécifications.
    
    Args:
        plan_txt (str): Texte du plan de projet
        crew_spec_dict (dict): Dictionnaire de spécifications de l'équipe
    
    Returns:
        str: Chemin vers le dossier de la crew créée
    """
    # Création du dossier pour la crew avec slug
    project_title = crew_spec_dict.get("project_title", "default-project")
    slug = kebab_case(project_title)
    crew_dir = os.path.join("generated_crews", slug)
    os.makedirs(crew_dir, exist_ok=True)
    
    # Écriture du plan.md
    with open(os.path.join(crew_dir, "plan.md"), "w", encoding="utf-8") as f:
        f.write(plan_txt)
    
    # Création du fichier crew_exec.py
    crew_exec_content = """import os
import datetime
from crewai import Agent, Task, Crew, Process
from langchain_anthropic import ChatAnthropic

# Initialisation du modèle LLM avec température 0.4
llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.4)

# Définition des agents
"""
    
    # Ajout des agents au contenu du fichier
    for i, agent_spec in enumerate(crew_spec_dict.get("agents", [])):
        agent_var = f"agent{i+1}"
        crew_exec_content += f"""
{agent_var} = Agent(
    role="{agent_spec.get('role', 'Agent')}",
    goal="{agent_spec.get('goal', 'Complete assigned tasks')}",
    backstory="{agent_spec.get('backstory', 'Experienced professional')}",
    llm=llm,
    verbose=True
)
"""
    
    # Ajout des tâches au contenu du fichier
    crew_exec_content += "\n# Définition des tâches\n"
    
    for i, task_spec in enumerate(crew_spec_dict.get("tasks", [])):
        agent_index = task_spec.get("agent_index", 0)
        agent_var = f"agent{agent_index+1}"
        
        crew_exec_content += f"""
task{i+1} = Task(
    description="{task_spec.get('description', 'Complete the task')}",
    expected_output="{task_spec.get('expected_output', 'Completed task')}",
    agent={agent_var}
)
"""
    
    # Ajout de la liste des tâches
    crew_exec_content += "\n# Liste de toutes les tâches\n"
    tasks_list = ", ".join([f"task{i+1}" for i in range(len(crew_spec_dict.get("tasks", [])))])
    crew_exec_content += f"ALL_TASKS = [{tasks_list}]\n\n"
    
    # Ajout du choix de processus (correction ici)
    process_type = "Process.hierarchical" if crew_spec_dict.get("structure") == "hierarchical" else "Process.sequential"
    
    # Fonction d'exécution
    crew_exec_content += f"""
def exec_crew():
    \"\"\"
    Exécute la crew avec le processus et les tâches définis.
    
    Returns:
        dict: Résultats de l'exécution de la crew
    \"\"\"
    # Création de la crew
    crew = Crew(
        agents=[{", ".join([f"agent{i+1}" for i in range(len(crew_spec_dict.get("agents", [])))])}],
        tasks=ALL_TASKS,
        process={process_type},
        verbose=True
    )
    
    # Création du dossier de logs
    log_dir = os.path.join(os.path.dirname(__file__), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Génération du timestamp pour le nom du fichier
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"crew_log_{{timestamp}}.txt")
    
    print(f"Démarrage de la crew '{project_title}'... Résultats dans {{log_file}}")
    
    # Exécution de la crew
    results = crew.kickoff()
    
    # Écriture des résultats dans le fichier de log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== Exécution de la crew '{project_title}' - {{timestamp}} ===\\n\\n")
        
        # Log des résultats finaux
        f.write("=== RÉSULTATS FINAUX ===\\n\\n")
        f.write(str(results))
    
    print(f"Exécution terminée. Logs sauvegardés dans {{log_file}}")
    return results

if __name__ == "__main__":
    # Si ce script est exécuté directement, lancer la crew
    exec_crew()
"""
    
    # Écriture du fichier crew_exec.py
    with open(os.path.join(crew_dir, "crew_exec.py"), "w", encoding="utf-8") as f:
        f.write(crew_exec_content)
    
    print(f"Crew '{project_title}' créée avec succès dans le dossier {crew_dir}")
    return crew_dir

if __name__ == "__main__":
    # Exemple d'utilisation pour tester
    test_plan_txt = "# Plan de test\n\nCeci est un plan de test pour vérifier le fonctionnement."
    test_crew_spec_dict = {
        "project_title": "Plateforme E-commerce",
        "structure": "hierarchical",
        "agents": [
            {
                "role": "Chef de Projet",
                "goal": "Superviser le développement du projet",
                "backstory": "Chef de projet expérimenté ayant géré de nombreux projets e-commerce."
            },
            {
                "role": "Développeur Frontend",
                "goal": "Créer une interface utilisateur intuitive",
                "backstory": "Expert en UI/UX avec une passion pour les expériences utilisateur fluides."
            },
            {
                "role": "Développeur Backend",
                "goal": "Développer une API robuste et sécurisée",
                "backstory": "Spécialiste des architectures distribuées et systèmes hautement disponibles."
            }
        ],
        "tasks": [
            {
                "description": "Planifier les phases du projet",
                "expected_output": "Planning détaillé avec jalons",
                "agent_index": 0
            },
            {
                "description": "Concevoir les maquettes de l'interface",
                "expected_output": "Maquettes et wireframes validés",
                "agent_index": 1
            },
            {
                "description": "Développer le modèle de données",
                "expected_output": "Schéma de base de données",
                "agent_index": 2
            }
        ]
    }
    
    # Décommentez pour tester
    # create_crew(test_plan_txt, test_crew_spec_dict)