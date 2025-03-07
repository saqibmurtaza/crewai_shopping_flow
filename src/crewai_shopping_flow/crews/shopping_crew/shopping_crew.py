from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_shopping_flow.tools.custom_tool import (
    SearchTool,
    RecommendationTool,
    InteractionTool,
    CartManagerTool,
    CheckoutTool,
    SupportTool,
)

@CrewBase
class ShoppingCrew:
    """Shopping Crew to assist users from product search to checkout."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    llm = "gemini/gemini-1.5-flash"

    @agent
    def search_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["search_agent"],
            llm=self.llm,
            tools=[SearchTool()],
            verbose=True,
        )

    @agent
    def recommendation_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["recommendation_agent"],
            llm=self.llm,
            tools=[RecommendationTool()],
            verbose=True,
        )

    @agent
    def interaction_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["interaction_agent"],
            llm=self.llm,
            tools=[InteractionTool()],
            verbose=True,
        )

    @agent
    def cart_manager(self) -> Agent:
        return Agent(
            config=self.agents_config["cart_manager"],
            llm=self.llm,
            tools=[CartManagerTool()],
            verbose=True,
        )

    @agent
    def checkout_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["checkout_agent"],
            llm=self.llm,
            tools=[CheckoutTool()],
            verbose=True,
        )

    @agent
    def support_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["support_agent"],
            llm=self.llm,
            tools=[SupportTool()],
            verbose=True,
        )

    @task
    def search_task(self) -> Task:
        return Task(
            config=self.tasks_config["search_task"],
            agent=self.search_agent(),
        )

    @task
    def recommendation_task(self) -> Task:
        return Task(
            config=self.tasks_config["recommendation_task"],
            agent=self.recommendation_agent()
        )

    @task
    def interaction_task(self) -> Task:
        return Task(
            config=self.tasks_config["interaction_task"],
            agent=self.interaction_agent()
        )

    @task
    def cart_task(self) -> Task:
        return Task(
            config=self.tasks_config["cart_task"],
            agent=self.cart_manager()
        )

    @task
    def checkout_task(self) -> Task:
        return Task(
            config=self.tasks_config["checkout_task"],
            agent=self.checkout_agent()
        )

    @task
    def support_task(self) -> Task:
        return Task(
            config=self.tasks_config["support_task"],
            agent=self.support_agent()
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Shopping Crew."""
        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
        )
