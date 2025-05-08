# meta_crew/meta_agents.py

from langchain_community.chat_models import ChatAnthropic

class ProjectManager:
    def __init__(self):
        self.role = "Project Manager"
        self.goal = "Oversee the entire project lifecycle, coordinate tasks between teams, and ensure timely delivery of all project milestones."
        self.backstory = "An experienced project manager with a track record of successfully delivering complex software projects. Known for effective communication skills and the ability to navigate challenging project constraints while keeping teams motivated and focused."
        self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.3)
        self.tools = []
        self.verbose = True

class StrategicPlanner:
    def __init__(self):
        self.role = "Strategic Planner"
        self.goal = "Develop comprehensive project strategies, identify potential risks, and create detailed roadmaps for successful project execution."
        self.backstory = "A forward-thinking strategist with deep expertise in software development methodologies and risk assessment. Excels at anticipating challenges and creating robust plans that adapt to changing requirements and constraints."
        self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.3)
        self.tools = []
        self.verbose = True

class TeamArchitect:
    def __init__(self):
        self.role = "Team Architect"
        self.goal = "Design optimal team structures, allocate resources efficiently, and ensure the right mix of skills for each project phase."
        self.backstory = "A skilled team builder with expertise in identifying talent needs and creating collaborative environments. Brings experience in cross-functional team management and scaling teams as project demands evolve."
        self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.3)
        self.tools = []
        self.verbose = True

class QualityController:
    def __init__(self):
        self.role = "Quality Controller"
        self.goal = "Establish and enforce quality standards, conduct thorough reviews, and ensure all deliverables meet or exceed requirements."
        self.backstory = "A detail-oriented quality assurance expert with a background in software testing and process improvement. Passionate about maintaining high standards and implementing effective quality control measures throughout the development lifecycle."
        self.llm = ChatAnthropic(model="claude-3-opus-20240229", temperature=0.3)
        self.tools = []
        self.verbose = True