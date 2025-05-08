# meta_crew/meta_tasks.py

from meta_crew.meta_agents import strategic_planner, team_architect, project_manager, quality_controller
from crewai import Task

# Tâche 1: Analyse des besoins (StrategicPlanner)
task1 = Task(
    description="Analyser en profondeur les exigences du projet et identifier les contraintes principales.",
    expected_output="Liste des besoins fonctionnels, non-fonctionnels, contraintes et risques potentiels",
    agent=strategic_planner
)

# Tâche 2: Plan détaillé (StrategicPlanner)
task2 = Task(
    description="Élaborer un plan détaillé du projet avec les étapes, jalons et échéances.",
    expected_output="Chronologie du projet, étapes clés, livrables, estimation des ressources et stratégies de mitigation des risques",
    agent=strategic_planner
)

# Tâche 3: Design équipe (TeamArchitect)
task3 = Task(
    description="Concevoir la structure optimale de l'équipe pour répondre aux besoins du projet.",
    expected_output="Composition détaillée de l'équipe, rôles et responsabilités, matrice de compétences requises, plan de communication interne",
    agent=team_architect
)

# Tâche 4: Validation du plan (ProjectManager)
task4 = Task(
    description="Évaluer et valider le plan de projet et la structure d'équipe proposés.",
    expected_output="Analyse critique du plan, points forts et points faibles identifiés, recommandations d'ajustements, validation finale",
    agent=project_manager
)

# Tâche 5: Relecture finale (QualityController)
task5 = Task(
    description="Effectuer une revue complète de tous les livrables pour assurer leur qualité et cohérence.",
    expected_output="Rapport de contrôle qualité, liste des non-conformités, suggestions d'améliorations, certification de conformité finale",
    agent=quality_controller
)

# Liste de toutes les tâches
ALL_TASKS = [task1, task2, task3, task4, task5]