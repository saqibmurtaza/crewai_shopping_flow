from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_flow.tools.custom_tool import (
    SearchTool
   # Other tools as needed...
)
from crewai_flow.crews.shopping_crew.models import SearchResults

@CrewBase
class ShoppingCrew:
    """Shopping Crew to assist users from product search to checkout."""
    
    search_tool = SearchTool()

    @agent
    def search_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["search_agent"],
            tools=[self.search_tool],
            verbose=True,
        )

    @agent
    def recommendation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["recommendation_agent"],
        )

    @agent
    def interaction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["interaction_agent"],
            verbose=True
        )

    @task
    def search_task(self) -> Task:
        return Task(
            config=self.tasks_config["search_products"],
            agent=self.search_agent(),
            allow_delegation=False,
            output_type=SearchResults
        )

    @task
    def recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config["recommend_products"],
            agent=self.recommendation_agent(),
            output_type=SearchResults
        )

    @task
    def interaction_task(self) -> Task:
        return Task(
            config=self.tasks_config["interaction_task"],
            agent=self.interaction_agent()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Shopping Crew."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,    # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
