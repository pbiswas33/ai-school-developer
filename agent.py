import os
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from langsmith import traceable
from langchain_community.tools.shell.tool import ShellTool
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
import subprocess

@tool
def create_react_app_with_vite():
    """Creates a new React application using Vite in the 'app' directory."""
    # Fill in the implementation here
    pass

@tool
def create_directory(directory: str):
    """Creates a new writable directory with the given name if it does not exist."""
    # Fill in the implementation here
    pass

@tool
def find_file(filename: str, path: str):
    """Recursively searches for a file in the given path."""
    # Fill in the implementation here
    pass

@tool
def create_file(filename: str, content: str = "", directory=ROOT_DIR, file_type: str = ""):
    """Creates a new file with specified file type and content in the specified directory."""
    # Fill in the implementation here
    pass

@tool
def update_file(filename: str, content: str, directory: str = ""):
    """Updates, appends, or modifies an existing file with new content."""
    # Fill in the implementation here
    pass

# List of tools to use
tools = [
    ShellTool(ask_human_input=True), 
    create_directory, 
    create_react_app_with_vite, 
    find_file, 
    create_file, 
    update_file
    # Add more tools if needed
]

# Configure the language model
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Set up the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert web developer.",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# Bind the tools to the language model
llm_with_tools = llm.bind_tools(tools)

# Create the agent
agent = (
    # Fill in the code to create the agent here
)

# Create the agent executor
agent_executor = (
    # Fill in the code to create the agent executor here
)

# Main loop to prompt the user
while True:
    user_prompt = input("Prompt: ")
    list(agent_executor.stream({"input": user_prompt}))
