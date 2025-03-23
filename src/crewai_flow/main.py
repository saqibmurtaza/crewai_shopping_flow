import chainlit as cl
from crewai_flow.crew_shopping_flow import ShoppingFlow


flow = ShoppingFlow()

@cl.on_message
async def handle_message(message):
    await flow.interaction_agent(message)

@cl.on_chat_start
async def start():
    await cl.Message(content="Welcome to our Furniture Shopping Assistant! What type of furniture are you looking for today?").send()
