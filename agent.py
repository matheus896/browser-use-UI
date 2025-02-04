from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent
from dotenv import load_dotenv
import asyncio

load_dotenv()

# Carregar o modelo de linguagem
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

async def main():
    agent = Agent(
        task="Compare the price of gpt-4o and DeepSeek-V3",
        llm=llm,
    )
    result = await agent.run()
    print(result)

#Run the AI agent
asyncio.run(main())