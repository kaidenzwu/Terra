from terra import Agent
import numpy as np
from urllib.request import urlopen
import re

def fast_fibonacci(n: str):
    n = int(n)
    if n == 0:
        return 0
    if n == 1:
        return 1

    # Matrix exponentiation method
    F = np.array([[1, 1],
                  [1, 0]], dtype=object)  # dtype=object for large numbers

    def matrix_power(matrix, exp):
        result = np.eye(2, dtype=object)  # Identity matrix
        base = matrix
        while exp > 0:
            if exp % 2 == 1:
                result = np.dot(result, base)
            base = np.dot(base, base)
            exp //= 2
        return result



    result_matrix = matrix_power(F, n-1)
    return result_matrix[0][0]  # Fibonacci number at position n

def get_cnn_headlines():
    url = "http://cnn.com"
    page = urlopen(url)
    html_bytes = page.read()
    html = html_bytes.decode("utf-8")

    pattern = "<span class=\"container__headline-text\" data-editable=\"headline\">.*?</span>"

    match_results = re.findall(pattern, html, re.IGNORECASE)
    match_results = [re.sub("<.*?>", "", element) for element in match_results]

    my_string = ','.join(match_results)

    return my_string

AGENTS = {}

def start_agent(name):
    """
    Creates an agent and binds it to a global variable name.
    """
    if name in AGENTS:
        return f"Agent '{name}' already exists."
    else:
        AGENTS[name] = Agent('phi4-mini')
        return f"Agent '{name}' created successfully."

def sys_prompt_agent(name, prompt):
    """
    System prompt the agent that is bound to global variable name.
    """
    if name in AGENTS:
        AGENTS[name].sys_prompt(prompt)
        return f"System prompt set for agent '{name}'."
    else:
        return f"Agent '{name}' does not exist."

def chat_agent(name, prompt):
    """
    Initiate a chat with the agent that is bound to global variable name.
    """
    if name in AGENTS:
        response = AGENTS[name].chat(prompt)
        return f"Agent '{name}' response: {response}"
    else:
        return f"Agent '{name}' does not exist."


help = Agent('phi4-mini')
help.sys_prompt('''
You can call tools. Specifically, when you want to call a tool, please output it in this format
<call tool>get_time()</call tool> or <call tool>fibonacci(n)</call tool>
                
Then, I will put the tool The returned results are given to you in this format
<tool return result>2025-03-23T19:28:50.5551361Z</tool ​​return result>
or <tool return result>8<tool return result>
''')
help.add_tool('start_agent', start_agent, 'This function creates an AI agent with a name.')
help.add_tool('sys_prompt_agent', sys_prompt_agent, 'This function system prompts an AI agent. You can use this to give an AI a personality.')
help.add_tool('chat_agent', chat_agent, 'This function generates a text response from an AI agent.')
#help.sys_prompt("You are a friendly AI agent with the capability of making new AI agents. Chat with the user in a friendly way and help them as necessary.")
help.add_tool('fast_fibbonacci', fast_fibonacci, 'This function quickly returns the value of a specific element in the fibbonacci sequence')
help.add_tool('get_cnn_headlines', get_cnn_headlines, 'this function gives you of Chicago Maroon newspaper headlines from 1892')
# print(help.chat('Create an AI agent that has the personality of Lord Voldemort.'))

while True:
    user_input = input()
    if user_input == "EXIT":
        break
    else:
        print(help.chat(user_input))

for item in help.get_log():
    print(item)
