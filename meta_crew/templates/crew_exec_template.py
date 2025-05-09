# meta_crew/templates/crew_exec_template.py

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
        return f"# Rapport de test\n\n{test_report_match.group(0).strip()}"
    
    return None

def exec_crew():
    """
    Exécute une crew pour le développement du projet.
    Cette fonction inclut une boucle d'auto-évaluation qui permet jusqu'à 2 itérations.
    
    Returns:
        dict: Résultats de l'exécution
    """
    # Vérifier que la clé API est disponible
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("Erreur: ANTHROPIC_API_KEY n'est pas définie dans les variables d'environnement.")
        print(f"Chemin du .env recherché: {dotenv_path}")
        sys.exit(1)
    
    # Initialisation du compteur d'itérations
    iteration_count = 0
    max_iterations = 2
    approved = False
    
    # Nom du projet
    project_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    
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
        print(f"Démarrage de l'itération {iteration_count}/{max_iterations}")
        
        # Création des agents avec des instructions améliorées
        project_manager = Agent(
            role="Project Manager",
            goal=f"Superviser et coordonner l'ensemble du projet {project_name}",
            backstory="Un chef de projet expérimenté avec une expertise dans la gestion de projets complexes.",
            llm=llm,
            verbose=True
        )
        
        developer = Agent(
            role="Développeur",
            goal=f"Implémenter des fichiers complets et fonctionnels pour le projet {project_name}",
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
            goal=f"Assurer la qualité et la fiabilité du projet {project_name}",
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
            goal=f"Évaluer la qualité globale du projet {project_name} et ses livrables",
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
            f"Implémentez les fonctionnalités de base du projet {project_name}. "
            "Il est CRUCIAL que vous fournissiez du code COMPLET, du début à la fin, "
            "sans aucune troncature ou section manquante. Votre réponse doit inclure :\n\n"
            "1. Une analyse des besoins et une description de l'architecture choisie\n"
            "2. Le code source COMPLET pour CHAQUE fichier nécessaire, en précisant clairement "
            "le nom de chaque fichier avant son contenu\n"
            "3. Une explication de l'implémentation et des instructions d'utilisation\n\n"
            "IMPORTANT : Assurez-vous que chaque fichier de code contient toutes les importations, "
            "toutes les définitions de classes/fonctions, et est prêt à être exécuté sans modification. "
            "Ne tronquez JAMAIS le code avec des commentaires comme '# reste du code...' "
            "ou des ellipses '...'."
        )
        
        # Instructions pour le testeur afin de créer des rapports de test complets
        test_instructions = (
            f"Testez les fonctionnalités implémentées du projet {project_name}. "
            "Il est CRUCIAL que vous fournissiez un rapport de test COMPLET et DÉTAILLÉ. "
            "Votre réponse doit inclure :\n\n"
            "1. Une description détaillée de la méthodologie de test\n"
            "2. Des cas de test spécifiques avec entrées et sorties attendues\n"
            "3. Les résultats obtenus pour CHAQUE test, avec des exemples concrets\n"
            "4. Une analyse des performances et des limites identifiées\n"
            "5. Des recommandations d'amélioration spécifiques\n\n"
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
                process=Process.sequential,
                verbose=True
            )
            
            dev_test_results = dev_test_crew.kickoff()
            
            # Stocker les résultats
            all_results.append({
                "iteration": iteration_count,
                "dev_results": str(dev_test_results),
                "tasks": [dev_task, test_task]
            })
            
            # Extraction et sauvegarde du code depuis les résultats
            code_results = extract_code_from_response(str(dev_test_results))
            for filename, code in code_results.items():
                artifact_manager.save_code(filename, code)
            
            # Extraction et sauvegarde des résultats de test
            test_report = extract_test_report(str(dev_test_results))
            if test_report:
                artifact_manager.save_document("test_report.md", test_report)
            
            # Écrire les résultats dans un fichier pour référence
            with open(os.path.join(logs_dir, f"iteration_{iteration_count}_results.txt"), "w", encoding="utf-8") as f:
                f.write(str(dev_test_results))
            
            # Si c'est la dernière itération, on n'a pas besoin d'évaluation
            if iteration_count >= max_iterations:
                # Si c'est la dernière itération, on considère que c'est approuvé
                approved = True
                continue
            
            # Préparer la description de la tâche d'auto-évaluation avec les résultats précédents
            review_description = (
                f"Examiner les livrables de l'itération {iteration_count} du projet {project_name} "
                f"et évaluer si le projet répond aux exigences. Votre rapport doit être COMPLET et DÉTAILLÉ. "
                f"Analysez la qualité du code, la couverture des tests et la fonctionnalité globale. "
                f"S'il y a des problèmes majeurs, incluez le mot 'retry' dans votre réponse. "
                f"Si le projet est approuvé, expliquez clairement pourquoi.\n\n"
                f"Voici les artefacts produits lors de cette itération :\n"
                f"{json.dumps(artifact_manager.list_artifacts(), indent=2)}\n\n"
                f"Voici un aperçu des résultats de l'itération actuelle :\n"
                f"{str(dev_test_results)[:2000]}..."
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
                artifact_manager.save_document(f"quality_report_iteration_{iteration_count}.md", quality_report)
                
                # Écrire les résultats dans un fichier pour référence
                with open(os.path.join(logs_dir, f"iteration_{iteration_count}_review.txt"), "w", encoding="utf-8") as f:
                    f.write(str(review_results))
                
                # Analyser le résultat pour décider si une autre itération est nécessaire
                review_result_str = str(review_results)
                if "retry" not in review_result_str.lower():
                    approved = True
                    print(f"Auto-évaluation approuvée à l'itération {iteration_count}")
                else:
                    print(f"Auto-évaluation recommande une nouvelle itération")
                    
                # Si c'est la dernière itération, indiquer que la limite est atteinte
                    if iteration_count >= max_iterations:
                        print(f"Nombre maximum d'itérations atteint ({max_iterations})")
                
            except Exception as review_error:
                print(f"Erreur lors de l'exécution de la tâche d'auto-évaluation: {str(review_error)}")
                # Enregistrer l'erreur dans un fichier de log
                error_log_path = os.path.join(logs_dir, "error.log")
                with open(error_log_path, "a", encoding="utf-8") as error_log:
                    error_log.write(f"=== ERREUR D'EXÉCUTION DE L'AUTO-ÉVALUATION - {datetime.datetime.now()} ===\n")
                    error_log.write(f"Itération: {iteration_count}\n")
                    error_log.write(f"Exception: {str(review_error)}\n\n")
                
                # Si c'est la dernière itération, sortir de la boucle
                if iteration_count >= max_iterations:
                    print(f"Nombre maximum d'itérations atteint ({max_iterations})")
                    
        except Exception as e:
            print(f"Erreur lors de l'exécution de la crew: {str(e)}")
            # Enregistrer l'erreur dans un fichier de log
            error_log_path = os.path.join(logs_dir, "error.log")
            with open(error_log_path, "a", encoding="utf-8") as error_log:
                error_log.write(f"=== ERREUR D'EXÉCUTION - {datetime.datetime.now()} ===\n")
                error_log.write(f"Itération: {iteration_count}\n")
                error_log.write(f"Exception: {str(e)}\n\n")
            
            # Si c'est la dernière itération, sortir de la boucle
            if iteration_count >= max_iterations:
                print(f"Nombre maximum d'itérations atteint ({max_iterations})")
    
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
        f.write(f"# Résumé du projet {project_name}\n\n")
        f.write(f"Date: {timestamp}\n\n")
        f.write(f"## Informations générales\n\n")
        f.write(f"- Nombre d'itérations: {iterations}\n")
        f.write(f"- Statut final: {'Approuvé' if approved else 'Nécessite des améliorations'}\n\n")
        
        f.write(f"## Agents utilisés\n\n")
        for agent in agents:
            f.write(f"### {agent.role}\n")
            f.write(f"- Objectif: {agent.goal}\n")
            f.write(f"- Expérience: {agent.backstory}\n\n")
        
        f.write(f"## Artefacts produits\n\n")
        f.write("| Fichier | Type |\n")
        f.write("| ------ | ---- |\n")
        for artifact in artifacts:
            artifact_type = "Code" if artifact.startswith("code/") else "Document" if artifact.startswith("docs/") else "Test"
            f.write(f"| {artifact} | {artifact_type} |\n")
        f.write("\n\n")
        
        f.write(f"## Tâches accomplies par itération\n\n")
        
        for iteration_data in results:
            iteration_num = iteration_data.get("iteration", "?")
            tasks = iteration_data.get("tasks", [])
            
            f.write(f"### Itération {iteration_num}\n\n")
            
            for task in tasks:
                short_description = task.description.split('\n')[0]
                f.write(f"#### {short_description}\n")
                f.write(f"- Agent responsable: {task.agent.role}\n")
                f.write(f"- Résultat attendu: {task.expected_output}\n\n")
        
        f.write(f"## Conclusion\n\n")
        if iterations == 1 and approved:
            f.write("Le projet a été approuvé dès la première itération, ce qui témoigne d'une excellente qualité des livrables.\n")
        elif approved:
            f.write(f"Le projet a nécessité {iterations} itérations avant d'être approuvé. Des améliorations ont été apportées suite aux retours du contrôleur qualité.\n")
        else:
            f.write(f"Le projet a atteint le nombre maximum d'itérations ({iterations}) sans être complètement approuvé. Des améliorations supplémentaires sont nécessaires.\n")
        
        f.write("\n## Instructions d'exécution\n\n")
        
        # Détecter automatiquement le type de projet et générer des instructions d'exécution
        python_files = [f for f in artifacts if f.endswith('.py') and f.startswith('code/')]
        js_files = [f for f in artifacts if f.endswith('.js') and f.startswith('code/')]
        html_files = [f for f in artifacts if f.endswith('.html') and f.startswith('code/')]
        
        if python_files:
            main_file = next((f for f in python_files if 'main' in f or 'app' in f), python_files[0])
            rel_path = os.path.join('artifacts', main_file)
            f.write(f"Pour exécuter ce projet Python :\n\n")
            f.write(f"```bash\n")
            f.write(f"cd {project_name}\n")
            f.write(f"python {rel_path}\n")
            f.write(f"```\n\n")
        
        if js_files and html_files:
            f.write(f"Pour exécuter ce projet web :\n\n")
            f.write(f"Ouvrez le fichier `artifacts/code/{next((f for f in html_files), '')}` dans votre navigateur.\n\n")

if __name__ == "__main__":
    # Exécution directe pour les tests
    exec_crew()