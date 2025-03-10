from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_shopping_flow.tools.custom_tool import (
    SearchTool,
    RecommendationTool,
    CartManagerTool,
    CheckoutTool,
    SupportTool,
)
from crewai_shopping_flow.crews.shopping_crew.llm_config import llm
from .models import SearchResults

@CrewBase
class ShoppingCrew:
    """Shopping Crew to assist users from product search to checkout."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    llm = llm

    search_tool = SearchTool()
    recommendation_tool = RecommendationTool()
    # cart_manager_tool = CartManagerTool()
    # checkout_tool = CheckoutTool()
    # support_tool = SupportTool()

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
            llm=self.llm,
            tools=[self.recommendation_tool],
            verbose=True,
        )

    @agent
    def interaction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["interaction_agent"],
            llm=self.llm,
            verbose=True
        )

    # @agent
    # def cart_manager(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["cart_manager"],
    #         llm=self.llm,
    #         tools=[self.cart_manager_tool],
    #         verbose=True,
    #     )

    # @agent
    # def checkout_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["checkout_agent"],
    #         llm=self.llm,
    #         tools=[self.checkout_tool],
    #         verbose=True,
    #     )

    # @agent
    # def support_agent(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config["support_agent"],
    #         llm=self.llm,
    #         tools=[self.support_tool],
    #         verbose=True,
    #     )

    @task
    def search_task(self) -> Task:
        return Task(
            config=self.tasks_config["search_products"],
            agent=self.search_agent(),
            output_json=SearchResults
        )

    @task
    def recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config["recommend_products"],
            agent=self.recommendation_agent()
        )

    @task
    def interaction_task(self) -> Task:
        return Task(
            config=self.tasks_config["interaction_task"],
            agent=self.interaction_agent(),
            output_json=SearchResults
        )

    # @task
    # def cart_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["cart_task"],
    #         agent=self.cart_manager()
    #     )

    # @task
    # def checkout_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["checkout_task"],
    #         agent=self.checkout_agent()
    #     )

    # @task
    # def support_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config["support_task"],
    #         agent=self.support_agent()
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the Shopping Crew."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
