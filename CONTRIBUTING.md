## 4. Fichier `setup.cfg`

```ini
[metadata]
name = madcrew
version = 0.1.0
description = Système automatisé de génération de projets avec des agents LLM
author = MAD-Crew Team
author_email = info@madcrew.example.com
license = MIT
classifiers =
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10

[options]
packages = find:
install_requires =
    langchain>=0.0.28
    langchain-anthropic>=0.0.5
    crewai>=0.28.0
    python-dotenv>=1.0.0

[options.entry_points]
console_scripts =
    madcrew=new_project:main