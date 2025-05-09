# meta_crew/meta_tasks.py

from meta_crew.meta_agents import strategic_planner, team_architect, project_manager, quality_controller
from crewai import Task

# Tâche 1: Analyse des besoins (StrategicPlanner)
task1 = Task(
    description="Analyser en profondeur les exigences du projet et identifier les contraintes principales. Soyez exhaustif et assurez-vous de couvrir tous les aspects fonctionnels et non-fonctionnels.",
    expected_output="Liste détaillée des besoins fonctionnels, non-fonctionnels, contraintes et risques potentiels. Format: document structuré avec sections clairement séparées.",
    agent=strategic_planner
)

# Tâche 2: Plan détaillé (StrategicPlanner)
task2 = Task(
    description="Élaborer un plan détaillé du projet avec les étapes, jalons et échéances. Incluez une chronologie précise et des livrables bien définis pour chaque phase.",
    expected_output="Chronologie complète du projet, étapes clés, livrables détaillés, estimation des ressources et stratégies de mitigation des risques. Format: document structuré avec diagramme de Gantt conceptuel.",
    agent=strategic_planner
)

# Tâche 3: Design équipe (TeamArchitect)
task3 = Task(
    description="Concevoir la structure optimale de l'équipe pour répondre aux besoins du projet. Précisez les compétences requises pour chaque rôle et les interactions entre les membres.",
    expected_output="Composition détaillée de l'équipe, rôles et responsabilités spécifiques, matrice de compétences requises, plan de communication interne. Format: organigramme avec descriptions de poste.",
    agent=team_architect
)

# Tâche 4: Validation du plan (ProjectManager)
task4 = Task(
    description="Évaluer et valider le plan de projet et la structure d'équipe proposés. Identifiez les forces, faiblesses, opportunités et menaces (SWOT) du plan actuel.",
    expected_output="Analyse critique complète du plan, points forts et faibles clairement identifiés, recommandations d'ajustements concrètes, validation finale avec conditions éventuelles. Format: rapport d'évaluation structuré.",
    agent=project_manager
)

# Tâche 5: Relecture finale (QualityController)
task5 = Task(
    description="Effectuer une revue complète de tous les livrables pour assurer leur qualité et cohérence. Vérifiez particulièrement la faisabilité technique, la clarté des objectifs et la complétude des spécifications.",
    expected_output="Rapport de contrôle qualité exhaustif, liste détaillée des non-conformités classées par gravité, suggestions d'améliorations concrètes, certification de conformité finale. Format: document structuré avec système de notation.",
    agent=quality_controller
)

# Liste de toutes les tâches
ALL_TASKS = [task1, task2, task3, task4, task5]