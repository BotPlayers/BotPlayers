from abc import abstractmethod
from typing import Any
import inspect
import re
import json
import openai
import tiktoken

from .util import print_in_color

WORLD_PARAM_NAME = 'self'
AGENT_NAME_PARAM_NAME = 'agent_name'

GPT_CALLABLE_FUNCTION_TABLE = dict()

TOKEN_ENCODING = tiktoken.encoding_for_model('gpt-3.5-turbo')


class agent_callable:
    """
    A decorator that registers a function as a callable for GPT to call.

    Args:
        role_name_filter: a regex string to filter the role name. Default to '.*'.
    """

    def __init__(self, role_name_filter: str = '.*'):
        self.role_name_filter = role_name_filter

    def __call__(self, function: callable):
        global GPT_CALLABLE_FUNCTION_TABLE

        # Get the parameters of the function
        signature = inspect.signature(function)
        parameters = signature.parameters
        has_world_param = WORLD_PARAM_NAME in parameters
        has_agent_name_param = AGENT_NAME_PARAM_NAME in parameters
        parameters_clean = {
            name: parameter for name, parameter in parameters.items()
            if name not in {WORLD_PARAM_NAME, AGENT_NAME_PARAM_NAME}}

        required_parameters = []
        for name, parameter in parameters_clean.items():
            if parameter.default is inspect.Parameter.empty:
                required_parameters.append(name)

        # Get the type of each parameter by parsing the signature
        json_schema_types = dict()
        type_annotation_to_json_schema_type = {
            str: 'string',
            int: 'integer',
            float: 'number',
            bool: 'boolean',
        }
        for name, parameter in parameters_clean.items():
            if parameter.annotation is not inspect.Parameter.empty:
                type_annotation = parameter.annotation
                json_schema_types[name] = type_annotation_to_json_schema_type.get(
                    type_annotation, 'string')

        # Get the description of each parameter by parsing the doc
        doc = function.__doc__
        if doc is None:
            doc = ''
        parameter_descriptions = {}
        for name in parameters_clean:
            pattern = rf'{name}:(.*)'
            match = re.search(pattern, doc)
            if match:
                parameter_descriptions[name] = match.group(1).strip()

        # Get function description from function doc string
        if 'Args:' in doc:
            function_description = doc.split('Args:')[0].strip()
        elif 'Returns:' in doc:
            function_description = doc.split('Returns:')[0].strip()
        else:
            function_description = doc.strip()
        function_description = '\n'.join(
            [line.strip() for line in function_description.split('\n') if len(line.strip()) > 0])

        # Register the function
        func_sig = {
            'name': function.__name__,
            'description': function_description,
            'parameters': {
                'type': 'object',
                'properties': {
                    name: {
                        'type': json_schema_types.get(name, 'string'),
                        'description': parameter_descriptions.get(name, ''),
                    } for name in parameters_clean
                },
                'required': required_parameters,
            },
        }
        GPT_CALLABLE_FUNCTION_TABLE[function.__name__] = {
            'sig': func_sig,
            'function': function,
            'has_world_param': has_world_param,
            'has_agent_name_param': has_agent_name_param,
            'role_name_filter': self.role_name_filter,
        }
        return function


def stream_chat_completion(engine: str, messages: list, print_output: bool = True, **kwargs):
    resp = openai.ChatCompletion.create(
        model=engine,
        messages=messages,
        stream=True,
        **kwargs
    )
    role = ''
    content = ''
    function_call = dict()
    for chunk in resp:
        for c in chunk['choices']:
            delta = c['delta']
            if 'role' in delta:
                role = delta['role']

            if 'function_call' in delta:
                for key, val in delta['function_call'].items():
                    if key not in function_call:
                        function_call[key] = val
                    else:
                        function_call[key] += val

            if 'content' in delta:
                if len(content) == 0 and delta['content'] == '\n\n' or delta['content'] is None:
                    continue
                content += delta['content']
                if print_output:
                    print_in_color(delta['content'], 'yellow', end='')

    if len(content) > 0 and print_output:
        print()

    message = dict()
    message['role'] = role
    message['content'] = content
    if len(function_call) > 0:
        message['function_call'] = function_call
    return message


class Agent:
    """ An agent that can think and act.
    """
    name: str
    role: str = 'agent'
    memory: list[dict] = []
    engine: str = 'gpt-3.5-turbo-16k'
    engine_args: dict = dict(temperature=1.0)
    function_call_repeats: int = 1
    ignore_none_function_messages: bool = True

    def __init__(self, name: str, prompt: str,
                 engine: str = 'gpt-3.5-turbo-16k', role: str = 'agent',
                 function_call_repeats: int = 1,
                 ignore_none_function_messages: bool = True):
        self.name = name
        self.engine = engine
        self.role = role
        self.memory = [
            {"role": "system",  "content": prompt},
        ]
        self.function_call_repeats = function_call_repeats
        self.ignore_none_function_messages = ignore_none_function_messages
        self.callable_functions = self._callable_function_descriptions()

    def _callable_function_descriptions(self):
        """
        Get the descriptions of all GPT callable functions.
        """
        ds = []
        for _, function in GPT_CALLABLE_FUNCTION_TABLE.items():
            role_name_filter = function['role_name_filter']
            # use regex to match role name filter
            if not re.match(role_name_filter, self.role):
                continue
            ds.append(function['sig'])
        return ds

    def _call_gpt_function(self, function_call: dict, world: Any = None):
        """
        Call a GPT function.
        """
        function_name = function_call["name"]

        if function_name not in GPT_CALLABLE_FUNCTION_TABLE:
            return {'error': f'"{function_name}" is not a callable function.'}

        try:
            print_in_color(
                f'    {self.name} is calling function {function_name} ...', 'blue')
            function_info = GPT_CALLABLE_FUNCTION_TABLE[function_name]
            function_to_call = function_info['function']
            has_world_param = function_info['has_world_param']
            has_agent_name_param = function_info['has_agent_name_param']

            function_args = function_call["arguments"]
            if function_args is None:
                function_args = dict()
            else:
                function_args: dict = json.loads(function_args)

            print_in_color(f'        with arguments {function_args}', 'blue')
            if has_world_param:
                function_args[WORLD_PARAM_NAME] = world
            if has_agent_name_param:
                function_args[AGENT_NAME_PARAM_NAME] = self.name

            function_response = function_to_call(**function_args)
            if function_response is None:
                return None

            print_in_color(f'        response: {function_response}', 'blue')
            return function_response
        except Exception as e:
            print_in_color(f'        error: {e}', 'red')
            return {'error': str(e)}

    def receive_message(self, message: dict):
        print_in_color(
            f'{self.name} received a message: {message["content"]}', 'green')
        self.memory.append(message)

    def think_and_act_in_world(self, world: Any):
        for _ in range(self.function_call_repeats):
            print_in_color(f'{self.name} >> ', 'yellow')
            if self.callable_functions:
                new_message = stream_chat_completion(
                    engine=self.engine,
                    messages=self.memory,
                    print_output=not self.ignore_none_function_messages,
                    functions=self.callable_functions,
                    function_call="auto",
                    **self.engine_args
                )
            else:
                new_message = stream_chat_completion(
                    engine=self.engine,
                    messages=self.memory,
                    print_output=not self.ignore_none_function_messages,
                    **self.engine_args
                )

            if new_message.get("function_call"):
                function_response = self._call_gpt_function(
                    new_message["function_call"], world=world)
                if function_response is None:
                    function_response = 'done'
                self.memory.append(new_message)
                self.memory.append(
                    {
                        "role": "function",
                        "name": new_message["function_call"]["name"],
                        "content": json.dumps(function_response, default=str),
                    }
                )
            else:
                if not self.ignore_none_function_messages:
                    self.memory.append(new_message)
                break
