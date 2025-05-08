# meta_crew/meta_agents.py

import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from crewai import Agent  # Importation de la classe Agent de crewAI

# Chargement des variables d'environnement
load_dotenv()

# Création du modèle de langage
llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.3)

# Définition des agents avec la classe Agent de crewAI
project_manager = Agent(
    role="Project Manager",
    goal="Oversee the entire project lifecycle, coordinate tasks between teams, and ensure timely delivery of all project milestones.",
    backstory="An experienced project manager with a track record of successfully delivering complex software projects. Known for effective communication skills and the ability to navigate challenging project constraints while keeping teams motivated and focused.",
    llm=llm,
    tools=[],
    verbose=True
)

strategic_planner = Agent(
    role="Strategic Planner",
    goal="Develop comprehensive project strategies, identify potential risks, and create detailed roadmaps for successful project execution.",
    backstory="A forward-thinking strategist with deep expertise in software development methodologies and risk assessment. Excels at anticipating challenges and creating robust plans that adapt to changing requirements and constraints.",
    llm=llm,
    tools=[],
    verbose=True
)

team_architect = Agent(
    role="Team Architect",
    goal="Design optimal team structures, allocate resources efficiently, and ensure the right mix of skills for each project phase.",
    backstory="A skilled team builder with expertise in identifying talent needs and creating collaborative environments. Brings experience in cross-functional team management and scaling teams as project demands evolve.",
    llm=llm,
    tools=[],
    verbose=True
)

quality_controller = Agent(
    role="Quality Controller",
    goal="Establish and enforce quality standards, conduct thorough reviews, and ensure all deliverables meet or exceed requirements.",
    backstory="A detail-oriented quality assurance expert with a background in software testing and process improvement. Passionate about maintaining high standards and implementing effective quality control measures throughout the development lifecycle.",
    llm=llm,
    tools=[],
    verbose=True
)