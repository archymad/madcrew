#!/usr/bin/env python
# new_project.py

import argparse
import os
import sys
import subprocess
import json

def main():
    """
    Point d'entrée principal pour l'outil en ligne de commande MAD-Crew.
    Permet de lancer un nouveau projet avec des paramètres spécifiques.
    """
    parser = argparse.ArgumentParser(description="MAD-Crew Project Generator")
    parser.add_argument("--title", "-t", required=True, help="Titre du projet")
    parser.add_argument("--mode", "-m", default="hierarchical", 
                        choices=["hierarchical", "agile"],
                        help="Mode de fonctionnement de la crew (hierarchical ou agile)")
    
    # Options supplémentaires
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Afficher les logs détaillés pendant l'exécution")
    
    args = parser.parse_args()
    
    # Créer le répertoire de configuration s'il n'existe pas
    os.makedirs(".madcrew", exist_ok=True)
    
    # Enregistrer les paramètres du projet
    project_config = {
        "project_title": args.title,
        "structure": args.mode,
        "verbose": args.verbose,
        "agents": [
            {
                "role": "Chef de Projet",
                "goal": "Superviser l'ensemble du projet et assurer sa réussite",
                "backstory": "Gestionnaire expérimenté avec une spécialisation dans les projets complexes."
            },
            {
                "role": "Développeur",
                "goal": "Implémenter les fonctionnalités selon les spécifications",
                "backstory": "Expert technique avec des compétences en développement web et architecture logicielle."
            },
            {
                "role": "Testeur",
                "goal": "Assurer la qualité et la fiabilité du produit final",
                "backstory": "Spécialiste en assurance qualité avec une attention particulière aux détails."
            }
        ],
        "tasks": [
            {
                "description": "Analyser les besoins et définir le périmètre du projet",
                "expected_output": "Document de spécifications fonctionnelles",
                "agent_index": 0
            },
            {
                "description": "Développer les fonctionnalités principales",
                "expected_output": "Code source fonctionnel",
                "agent_index": 1
            },
            {
                "description": "Tester l'ensemble des fonctionnalités et rapporter les bugs",
                "expected_output": "Rapport de test détaillé",
                "agent_index": 2
            }
        ]
    }
    
    # Enregistrer la configuration
    config_path = os.path.join(".madcrew", "current_project.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(project_config, f, indent=2, ensure_ascii=False)
    
    print(f"Configuration du projet '{args.title}' enregistrée.")
    print(f"Mode: {args.mode}")
    
    # Déterminer le chemin absolu vers run_meta.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_meta_path = os.path.join(script_dir, "run_meta.py")
    
    print(f"Lancement de la méta-crew pour le projet '{args.title}'...")
    
    # Définir les variables d'environnement pour run_meta.py
    env = os.environ.copy()
    env["MADCREW_PROJECT_TITLE"] = args.title
    env["MADCREW_PROJECT_MODE"] = args.mode
    env["MADCREW_CONFIG_PATH"] = config_path
    
    # Exécuter run_meta.py
    try:
        process = subprocess.run([sys.executable, run_meta_path], 
                                env=env, 
                                check=True)
        
        if process.returncode == 0:
            print(f"Le projet '{args.title}' a été généré avec succès!")
            print(f"Vous pouvez trouver les résultats dans 'generated_crews/{args.title.lower().replace(' ', '-')}'")
        else:
            print(f"Une erreur est survenue lors de la génération du projet. Code: {process.returncode}")
            
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de run_meta.py: {e}")
        sys.exit(1)
        
    return 0

if __name__ == "__main__":
    sys.exit(main())