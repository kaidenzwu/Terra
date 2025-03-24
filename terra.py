import ollama
import re
import inspect
from ollama import ChatResponse
from datetime import datetime
import os.path

def get_time():
    return datetime.utcnow().isoformat(timespec='microseconds') + 'Z'

def timestamp_to_datetime(timestamp: str):
    # Convert ISO 8601 timestamp with 7-digit precision
    return datetime.strptime(timestamp[:-1], "%Y-%m-%dT%H:%M:%S.%f")

def time_difference_in_ns(timestamp1: str, timestamp2: str):
    dt1 = timestamp_to_datetime(timestamp1)
    dt2 = timestamp_to_datetime(timestamp2)
    
    # Calculate the difference in seconds and convert to nanoseconds
    delta_ns = int((dt2 - dt1).total_seconds() * 1e9)
    return delta_ns

def default_format_tool_instructions(tool_name: str, tool: callable, instructions: str):
    # Extract parameter details from the tool
    signature = inspect.signature(tool)
    param_list = []
    
    for name, param in signature.parameters.items():
        if param.default is inspect.Parameter.empty:
            param_list.append(name)  # Required parameter
        else:
            param_list.append(f"{name}={param.default}")  # Optional parameter with default
    
    # Join parameters for formatting
    param_str = ', '.join(param_list)
    
    # Return formatted instructions
    return f'''You have been given access to the tool "{tool_name}({param_str})". {instructions}
    Please call this function by using the following format: <call tool>{tool_name}({param_str})</call tool>'''

class Agent():

    save_path = '/Users/kaiden/PythonLearning/logs'
    my_log_file = os.path.join(save_path, 'log_' + get_time() +'.txt')  
    f = open(my_log_file, "w")
    
    def __init__(self, model: str):
        '''
        Initiate the model with the model used and
        blank memory and debug log.
        '''
        self.model = model
        self.memory = []
        self.log = [{
            'time': get_time(),
            'action': '__init__',
            'prompt': model,
            'other': {}
        }] # time, action, prompt, other

        self.tools = {}
        self.format_tool_instructions = default_format_tool_instructions

    def add_tool(self, tool_name: str, tool: callable, instructions: str = None):
        self.tools[tool_name] = {}
        self.tools[tool_name]['tool'] = tool
        self.tools[tool_name]['instructions'] = instructions
        # self.log.append({
        #     'time': get_time(),
        #     'action': 'add_tool',
        #     'prompt': tool_name,
        #     'other': {
        #         'instructions': instructions
        #     }
        # })
        self._add_to_log(get_time(), 'add_tool', tool_name, 'instructions:' + instructions)
        if instructions is not None:
            self.sys_prompt(self.format_tool_instructions(tool_name, tool, instructions))

    def sys_prompt(self, sys_prompt: str):
        self.memory.append(
            {
                'role': 'system',
                'content': sys_prompt
            }
        )
        # self.log.append({
        #     'time': get_time(),
        #     'action': 'sys_prompt',
        #     'prompt': sys_prompt,
        #     'other': {}
        # })
        self._add_to_log(get_time(), 'sys_prompt', sys_prompt, 'other')

    def chat(self, prompt: str):
        self.memory.append(
            {
                'role': 'user',
                'content': prompt
            }
        )
        
        start_time = get_time()
        user_content = ''

        # self.log.append({
        #     'time': start_time,
        #     'action': 'chat',
        #     'prompt': prompt,
        #     'other': {}
        # })

        self._add_to_log(get_time(), 'chat', prompt, 'other')
    

        while True:
            content = ''
            stream: ChatResponse = ollama.chat(model=self.model,messages=self.memory, stream=True)
            
            for chunk in stream:
                content += chunk.message.content
                tool_match = re.search(r'<call tool>(.*?)</call tool>', content)
                if tool_match:
                    tool_call = tool_match.group(1)
                    # break  # Stop stream when tool use is detected
            
            user_content += re.sub(r"<call tool>.*?</call tool>", "", content).strip()
            self.memory.append({'role': 'assistant', 'content': content})
            
            if tool_match:
                tool_name, *params = self._extract_tool_call(tool_call)

                # Handle commas inside strings
                joined_params = ','.join(params)
                params = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', joined_params)
                
                # Inject tool result back into memory
                try:
                    tool_result = f"<tool return result>{self.tools[tool_name]['tool'](*params)}</tool return result>"
                except Exception as e:
                    if tool_name not in self.tools:
                        tool_result = f"<tool return result>Error: Tool not defined.</tool return result>"
                    else:
                        tool_result = f"<tool return result>Error: {type(e)}</tool return result>"
                        print(tool_name)

                # self.log.append({
                #     'time': get_time(),
                #     'action': 'tool',
                #     'prompt': tool_call,
                #     'other': {
                #         'tool_result': tool_result,
                #         'tool_name': tool_name,
                #         'params': params,
                #     }
                # })

                self._add_to_log(get_time(), 'tool', tool_call, 'tool_result:' + tool_result + 'tool_name:' + tool_name + 'param:,' + str(params))
                self.sys_prompt(tool_result)
            else:
                break  # No more tool calls, exit loop
        end_time = get_time()

        # self.log.append({
        #     'time': end_time,
        #     'action': 'chat_end',
        #     'prompt': prompt,
        #     'other': {
        #         'total_duration': time_difference_in_ns(start_time, end_time)
        #     }
        # })
        self._add_to_log(get_time(), 'chat_end', prompt, 'total_duration:'+ str(time_difference_in_ns(start_time, end_time)/1000000000))
        return user_content
    
    def get_memory(self):
        return self.memory
    
    def get_log(self):
        return self.log
    
    def _add_to_log(self, time, action, prompt, other):
        log_entry = {
            'time': time,
            'action': action,
            'prompt': prompt,
            'other': other
        }
        self.log.append(log_entry)
        f = open(self.my_log_file, "a")
        f.write('\n' + str(log_entry))
        
    def _extract_tool_call(self, tool_call: str):
        """
        Extract tool name and parameters.
        Example Input: 'fibonnaci(5)'
        Output: ('fibonacci', ('5',))
        """
        tool_match = re.match(r'(\w+)\((.*?)\)', tool_call.strip())
        if tool_match:
            tool_name = tool_match.group(1)
            params = tuple(map(str.strip, tool_match.group(2).split(',')))
            return tool_name, *params
        return tool_call, ()