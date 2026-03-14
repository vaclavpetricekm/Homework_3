import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from visualizer import visualize



load_dotenv()


llm = ChatOpenAI(model="gpt-4o")


def get_tavily_mcp_url():
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY not found in environment")
    return f"https://mcp.tavily.com/mcp/?tavilyApiKey={api_key}"


async def get_mcp_tools():
    client = MultiServerMCPClient(
        {
            "tavily": {
                "url": get_tavily_mcp_url(),
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    return tools, client


# gmail tools
async def get_gmail_tools():
    client = MultiServerMCPClient(
        {
            "gmail": {
                "url": "https://gmail.mcp.claude.com/mcp",
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()
    return tools, client


# tavily haze chybu kdyz poslu topic=news takze to takhle obalim
def make_safe_tavily(tavily_tools):
    original = next(t for t in tavily_tools if "search" in t.name.lower())

    @tool
    async def tavily_search(query: str) -> str:
        """Search the web."""
        result = await original.ainvoke({"query": query, "topic": "general"})
        return str(result)

    return tavily_search


@tool
def calculator(expression: str) -> str:
    """Vypocita matematicky vyraz napr. 2+2"""
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {e}"


async def main():
    print("Initializing MCP connection to Tavily...")
    mcp_tools, mcp_client = await get_mcp_tools()
    print(f"Loaded {len(mcp_tools)} tools from Tavily MCP\n")

    try:
        gmail_tools, _ = await get_gmail_tools()
        print(f"Loaded {len(gmail_tools)} gmail tools")
    except Exception as e:
        print(f"gmail nefunguje: {e}")
        gmail_tools = []

    tools = [make_safe_tavily(mcp_tools), calculator] + list(gmail_tools)

    agent = create_react_agent(
        llm,
        tools=tools,
        prompt="You are a helpful assistant. Be concise and accurate.",
    )

    visualize(agent, "graph.png")

    while True:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_input}]}
        )
        print("Assistant:", result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
