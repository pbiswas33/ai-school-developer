import os
from collections import defaultdict
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
import jsmin
import csscompressor
import htmlmin
from github import Github
from typing import Optional

os.environ['OPENAI_API_KEY'] = ""
os.environ['LANGCHAIN_TRACING_V2'] = "true"
os.environ['LANGCHAIN_API_KEY'] = ""

ROOT_DIR = "./"
VALID_FILE_TYPES = {"py", "txt", "md", "cpp", "c", "java", "js", "html", "css", "ts", "json", "gradle", "sh"}
GITHUB_TOKEN = ""
GITHUB_USERNAME = ""

@tool
def create_react_app_with_vite():
    """
    This function creates a new React application using Vite in the 'app' directory located in the root.

    It navigates to the root directory, finds or creates the 'app' directory,
    and uses the npm 'create vite@latest' command to scaffold a new React project
    with Vite as the build tool and React as the template. If the process is
    successful, it prints a success message. If any subprocess command fails,
    it catches the CalledProcessError exception and prints an error message.
    """
    try:
        # Create a new Vite project in the app directory with React template
        subprocess.run(['npm', 'create', 'vite@latest', '.', '--template', 'react'], check=True)
        # Print success message if project creation is successful
        return f"Successfully created a new React app using Vite."
    except subprocess.CalledProcessError as e:
        # Print error message if any subprocess command fails
        return f"An error occurred: {e}"
    except Exception as e:
        # Print error message if any other exception occurs
        return f"An unexpected error occurred: {e}"

@tool
def create_directory(directory: str) -> str:
    """
    Create a new writable directory with the given directory name if it does not exist.
    If the directory exists, it ensures the directory is writable.

    Parameters:
    directory (str): The name of the directory to create.

    Returns:
    str: Success or error message.
    """
    if ".." in directory:
        return f"Cannot make a directory with '..' in path"
    try:
        os.makedirs(directory, exist_ok=True)
        subprocess.run(["chmod", "u+w", directory], check=True)
        return f"Directory successfully '{directory}' created and set as writeable."
    except subprocess.CalledProcessError as e:
        return f"Failed to create or set writable directory '{directory}': {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

@tool
def find_file(filename: str, path: str) -> Optional[str]:
    """
    Recursively searches for a file in the given path.
    Returns string of full path to file, or None if file not found.
    """
    # TODO handle multiple matches
    for root, dirs, files in os.walk(path):
        if filename in files:
            return os.path.join(root, filename)
    return None

@tool
def create_file(filename: str, content: str = "", directory=""):
    """Creates a new file and content in the specified directory."""
    # Validate file type
    try:
        file_stem, file_type = filename.split(".")
        assert file_type in VALID_FILE_TYPES
    except:
        return f"Invalid filename {filename} - must end with a valid file type: {VALID_FILE_TYPES}"
    directory_path = os.path.join(ROOT_DIR, directory)
    file_path = os.path.join(directory_path, filename)
    if not os.path.exists(file_path):
        try:
            with open(file_path, "w")as file:
                file.write(content)
            print(f"File '{filename}' created successfully at: '{file_path}'.")
            return f"File '{filename}' created successfully at: '{file_path}'."
        except Exception as e:
            print(f"Failed to create file '{filename}' at: '{file_path}': {str(e)}")
            return f"Failed to create file '{filename}' at: '{file_path}': {str(e)}"
    else:
        print(f"File '{filename}' already exists at: '{file_path}'.")
        return f"File '{filename}' already exists at: '{file_path}'."

@tool
def update_file(filename: str, content: str, directory: str = ""):
    """Updates, appends, or modifies an existing file with new content."""
    if directory:
        file_path = os.path.join(ROOT_DIR, directory, filename)
    else:
        file_path = find_file(filename, ROOT_DIR)

    if file_path and os.path.exists(file_path):
        try:
            with open(file_path, "a") as file:
                file.write(content)
            return f"File '{filename}' updated successfully at: '{file_path}'"
        except Exception as e:
            return f"Failed to update file '{filename}' at: '{file_path}' - {str(e)}"
    else:
        return f"File '{filename}' not found at: '{file_path}'"
# ------------------------------------------------ additional tools ------------------------------------------------
def minify_file(file_path):
    """Minifies the content of a given file based on its type."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if file_path.endswith('.js'):
            minified_content = jsmin.jsmin(content)
        elif file_path.endswith('.css'):
            minified_content = csscompressor.compress(content)
        elif file_path.endswith('.html'):
            minified_content = htmlmin.minify(content, remove_empty_space=True)
        else:
            print(f"Unsupported file type for minification: {file_path}")
            return
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(minified_content)
        
        print(f"File '{file_path}' minified successfully.")
    except Exception as e:
        print(f"Failed to minify file '{file_path}': {str(e)}")
        
def get_file_extension(file_name):
    return file_name.split('.')[-1]

def get_language_from_extension(extension):
    extension_map = {
        'py': 'Python',
        'js': 'JavaScript',
        'html': 'HTML',
        'css': 'CSS',
        'java': 'Java',
        'ts': 'Type Script',
        'cpp': 'C++',
        'c': 'C',
        'sh': 'Shell',
        'json': 'JSON',
        'gradle': 'Gradle'
    }
    return extension_map.get(extension, 'Others')

@tool
def minify_source_code(directory_path):
    """Minifies all supported files in the given directory and its subdirectories."""
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            minify_file(file_path)

@tool
def create_github_repo_and_upload_directory(repo_name: str, directory_path: str):
    """Creates a GitHub repository and uploads the contents of a directory to it."""
    g = Github(GITHUB_TOKEN)
    user = g.get_user()
    github_url = f"https://github.com/{GITHUB_USERNAME}/{repo_name}"
    # Create the repository on GitHub
    try:
        repo = user.create_repo(name=repo_name, private=False)
        print(f"Repository '{repo_name}' created successfully.")
    except Exception as e:
        return f"Failed to create repository '{repo_name}': {str(e)}"

    # Initialize git and push the directory contents to the new repository
    try:
        repo_url = repo.clone_url.replace("https://", f"https://{GITHUB_TOKEN}@")
        subprocess.run(["git", "init"], cwd=directory_path, check=True)
        subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=directory_path, check=True)
        subprocess.run(["git", "add", "."], cwd=directory_path, check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=directory_path, check=True)
        subprocess.run(["git", "push", "-u", "origin", "master"], cwd=directory_path, check=True)
        return f"Directory '{directory_path}' uploaded to repository '{repo_name}' successfully."
    except subprocess.CalledProcessError as e:
        return f"Failed to upload directory '{directory_path}' to repository '{repo_name}': {str(e)}"
@tool
def calculate_language_percentages(directory: str):
    """
    Calculates the percentage of characters for each programming language in the given directory.

    This function traverses through all files in the specified directory and its subdirectories,
    reads the content of each file, and calculates the total number of characters for each programming
    language based on the file extension. It then computes the percentage of characters for each language
    relative to the total number of characters across all files.

    Args:
        directory (str): The path to the directory to analyze.

    Returns:
        None: This function prints the percentage of characters for each programming language.
    """
    language_char_counts = defaultdict(int)
    total_characters = 0

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    char_count = len(content)
                    total_characters += char_count
                    extension = get_file_extension(file)
                    language = get_language_from_extension(extension)
                    language_char_counts[language] += char_count
            except Exception as e:
                print(f"Could not read file {file_path}: {e}")

    language_percentages = {language: (count / total_characters) * 100 for language, count in language_char_counts.items()}
    print("Languages and their percentages:")
    for language, percentage in language_percentages.items():
        print(f"{language.ljust(12)}: {percentage:.2f}%")
    
# List of tools to use
tools = [
    ShellTool(ask_human_input=True),
    create_directory,
    create_react_app_with_vite,
    find_file,
    create_file,
    update_file,
    minify_source_code,
    create_github_repo_and_upload_directory,
    calculate_language_percentages
]
# Configure the language model
llm = ChatOpenAI(model="gpt-4o", temperature=0)
# Set up the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert web developer as well as an application developer.",
        ),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


# Bind the tools to the language model
llm_with_tools = llm.bind_tools(tools)

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
    }
    | prompt
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Main loop to prompt the user
while True:
    user_prompt = input("Prompt: ")
    if user_prompt.lower() == "exit":
        break
    list(agent_executor.stream({"input": user_prompt}))