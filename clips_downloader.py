import ollama
import json
import glob
import os
from typing import List, Dict, Any

def search_text_files(keyword: str) -> str:
    """
    Searches for `keyword` in .txt files within the current directory.
    If keyword ends with .txt, searches for files with that name.
    Otherwise searches for the keyword in file contents.
    Returns matching file paths and line numbers.
    """
    results = []
    try:
        # Get the current working directory
        current_dir = os.getcwd()
        print(f"Searching in directory: {current_dir}")
        
        # If keyword ends with .txt, search for files with that name
        if keyword.lower().endswith('.txt'):
            file_path = os.path.join(current_dir, keyword)
            if os.path.exists(file_path):
                return f"Found file: {file_path}"
            else:
                return f"File not found: {file_path}"
        
        # Otherwise search for keyword in file contents
        txt_files = glob.glob(os.path.join(current_dir, "*.txt"))
        print(f"Found {len(txt_files)} .txt files")
        
        for file in txt_files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            results.append(f"{file} (Line {line_num}): {line.strip()}")
            except Exception as e:
                print(f"Error reading file {file}: {str(e)}")
                
        return "\n".join(results) if results else f"No matches found for '{keyword}' in any .txt files"
    except Exception as e:
        return f"Error during search: {str(e)}"

def execute_tool_call(tool_call: Dict[str, Any]) -> str:
    """
    Executes a tool call and returns the result.
    """
    function_name = tool_call['function']['name']
    args = tool_call['function']['arguments']  # Arguments are already a dict, no need for json.loads
    
    if function_name == 'search_text_files':
        return search_text_files(keyword=args['keyword'])
    else:
        return f"Unknown function: {function_name}"

def chat_with_tools(user_message: str) -> None:
    """
    Main function to handle chat with Ollama and tool execution.
    """
    # Register tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_text_files",
                "description": "Searches for keywords in text files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keyword": {"type": "string"}
                    },
                    "required": ["keyword"]
                }
            }
        }
    ]

    # Initialize chat with tool definitions
    response = ollama.chat(
        model='llama3.2:latest',
        messages=[{'role': 'user', 'content': user_message}],
        tools=tools,
        stream=True
    )

    # Process the response
    for chunk in response:
        if 'message' in chunk:
            message = chunk['message']
            
            # Handle tool calls
            if 'tool_calls' in message:
                for tool_call in message['tool_calls']:
                    result = execute_tool_call(tool_call)
                    print(f"🔍 Tool execution result:\n{result}")
            
            # Handle regular message content
            if 'content' in message and message['content']:
                print(f"🤖 Assistant: {message['content']}")

def main():
    """
    Main entry point for the application.
    """
    print("🤖 Welcome to the Ollama Tool Calling Demo!")
    print("Type 'exit' to quit")
    
    while True:
        user_input = input("\n👤 You: ").strip()
        if user_input.lower() == 'exit':
            break
            
        chat_with_tools(user_input)

if __name__ == "__main__":
    main()

