from typing import Any, List, Optional, Union
import inspect
import json
import re
import openai
from functools import lru_cache

from .util import print_in_color

SELF_PARAM_NAME = 'self'
AGENT_PARAM_NAME = 'agent'
AGENT_NAME_PARAM_NAME = 'agent_name'


def agent_callable(function):
    """ Decorator to mark a function as agent callable. """
    function.__agent_callable__ = True
    return function


class InteractiveSpace:
    def get_callable_functions(self):
        functions = []
        for func in dir(self):
            if func.startswith('__'):
                continue
            fun = getattr(self, func)
            if not hasattr(fun, '__agent_callable__'):
                continue
            if fun.__agent_callable__:
                functions.append(fun)
        return functions


@lru_cache()
def _parse_agent_callable_function(function):
    # Get the parameters of the function
    signature = inspect.signature(function)
    parameters = signature.parameters
    has_agent_param = AGENT_PARAM_NAME in parameters
    has_agent_name_param = AGENT_NAME_PARAM_NAME in parameters
    parameters_clean = {
        name: parameter for name, parameter in parameters.items()
        if name not in {SELF_PARAM_NAME, AGENT_PARAM_NAME, AGENT_NAME_PARAM_NAME}}

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
    func_info = {
        'sig': func_sig,
        'function': function,
        'has_agent_param': has_agent_param,
        'has_agent_name_param': has_agent_name_param,
    }
    return func_info


def _parse_interactive_objects(interactive_objects: List[Any]):
    """ Install interactive objects. """
    function_info_table = {}
    for obj in interactive_objects:
        if isinstance(obj, InteractiveSpace):
            functions = obj.get_callable_functions()
        else:
            assert hasattr(
                obj, '__agent_callable__'), f'Object {obj} is not agent callable.'
            assert obj.__agent_callable__, f'Object {obj} is not agent callable.'
            functions = [obj]
        for func in functions:
            assert func.__name__ not in function_info_table, f'Function {func.__name__} already registered.'
            function_info_table[func.__name__] = _parse_agent_callable_function(
                func)
    return function_info_table


def stream_chat_completion(engine: str, messages: List[dict], print_output: bool = True, **kwargs):
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


DEFAULT_FUNCTION_CALL_REPEATS = 10
DEFAULT_IGNORE_NONE_FUNCTION_MESSAGES = True


class Agent:
    """ An agent that can think and act.

    Args:
        name (str): The name of the agent.
        prompt (Union[str, list], optional): The prompt to initialize the agent's memory. Defaults to None.
        engine (str, optional): The GPT engine to use. Defaults to 'gpt-3.5-turbo-16k'.
        interactive_objects (list, optional): A list of interactive objects to install. Defaults to [].
            Each interactive object should be either an InteractiveSpace or an agent callable function (decorated by agent_callable).
        function_call_repeats (int, optional): The number of times to repeat function calls in agent.think_and_act().
        ignore_none_function_messages (bool, optional): Whether to ignore messages that does not involve function calling.
    """
    name: str = ''
    memory: List[dict] = []
    engine: str = 'gpt-3.5-turbo-16k'
    engine_args: dict = dict(temperature=1.0)
    interactive_objects: list = []
    callable_functions: dict = dict()
    function_call_repeats: int = 1
    ignore_none_function_messages: bool = True

    derived_from: Optional['Agent'] = None

    def __init__(self, name: str,
                 prompt: Optional[Union[str, list]] = None,
                 engine: str = 'gpt-3.5-turbo-16k',
                 interactive_objects: list = [],
                 function_call_repeats: int = DEFAULT_FUNCTION_CALL_REPEATS,
                 ignore_none_function_messages: bool = DEFAULT_IGNORE_NONE_FUNCTION_MESSAGES,
                 derived_from: Optional['Agent'] = None):
        self.name = name
        self.engine = engine

        if prompt is not None:
            if isinstance(prompt, str):
                self.memory = [
                    {"role": "system",  "content": prompt},
                ]
            elif isinstance(prompt, list):
                self.memory = prompt

        self.interactive_objects = interactive_objects
        self.callable_functions = _parse_interactive_objects(
            interactive_objects)

        self.function_call_repeats = function_call_repeats
        self.ignore_none_function_messages = ignore_none_function_messages
        self.derived_from = derived_from

    def derive_avatar(self, interactive_objects: Optional[list] = None,
                      function_call_repeats: Optional[int] = None,
                      ignore_none_function_messages: Optional[bool] = None):
        """
        Derive an avatar from the agent. 
        The avatar will inherit the agent's memory.
        But the history of the avatar will not be recorded in the agent's memory.

        Args:
            interactive_objects (list, optional): A list of interactive objects to install. Defaults to None.
            function_call_repeats (int, optional): The number of times to repeat function calls in agent.think_and_act(). Defaults to None.
            ignore_none_function_messages (bool, optional): Whether to ignore messages that does not involve function calling. Defaults to None.
        """
        if interactive_objects is None:
            interactive_objects = self.interactive_objects
        if function_call_repeats is None:
            function_call_repeats = self.function_call_repeats
        if ignore_none_function_messages is None:
            ignore_none_function_messages = self.ignore_none_function_messages
        return Agent(
            name=self.name,
            engine=self.engine,
            interactive_objects=interactive_objects,
            function_call_repeats=function_call_repeats,
            ignore_none_function_messages=ignore_none_function_messages,
            derived_from=self,
        )

    def print_memory(self):
        """ Print the agent's memory. """
        for idx, message in enumerate(self.memory):
            print_in_color(
                f'    [{idx}] {message["role"]}: {message["content"]}', 'green')

    def full_memory(self):
        if self.derived_from is None:
            return self.memory
        else:
            return self.derived_from.full_memory() + self.memory

    def print_full_memory(self):
        """ Print the agent's memory. """
        for idx, message in enumerate(self.full_memory()):
            print_in_color(
                f'    [{idx}] {message["role"]}: {message["content"]}', 'green')

    def add_interactive_object(self, interactive_object):
        """ Add an interactive object to the agent. """
        self.interactive_objects.append(interactive_object)
        self.callable_functions = _parse_interactive_objects(
            self.interactive_objects)
        return self

    def _callable_function_descriptions(self):
        """
        Get the descriptions of all GPT callable functions.
        """
        ds = []
        for _, function in self.callable_functions.items():
            ds.append(function['sig'])
        return ds

    def _call_function(self, function_call: dict):
        """
        Call a GPT function.
        """
        function_name = function_call["name"]

        if function_name not in self.callable_functions:
            return {'error': f'"{function_name}" is not a callable function.'}

        try:
            print_in_color(
                f'    {self.name} is calling function {function_name} ...', 'blue')
            function_info = self.callable_functions[function_name]
            function_to_call = function_info['function']
            has_agent_param = function_info['has_agent_param']
            has_agent_name_param = function_info['has_agent_name_param']

            function_args = function_call["arguments"]
            if function_args is None:
                function_args = dict()
            else:
                function_args: dict = json.loads(function_args)

            print_in_color(f'        with arguments {function_args}', 'blue')
            if has_agent_param:
                function_args[AGENT_PARAM_NAME] = self
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

    def receive_message(self, message: dict, print_output: bool = True):
        """
        Receive a message.

        Args:
            message (dict): The message to receive.
            print_output (bool, optional): Whether to print out the message. Defaults to True.
        """
        if print_output:
            print_in_color(
                f'{self.name} received a message: {message["content"]}', 'green')
        self.memory.append(message)
        return self

    def receive_messages(self, messages: List[dict], print_output: bool = True):
        """
        Receive a list of messages.

        Args:
            messages (List[dict]): The messages to receive.
            print_output (bool, optional): Whether to print out the messages. Defaults to True.
        """
        for message in messages:
            self.receive_message(message, print_output=print_output)
        return self

    def think_and_act(self):
        """
        Think and act.
        """
        for _ in range(self.function_call_repeats):
            print_in_color(f'{self.name} >> ', 'yellow')
            callable_functions = self._callable_function_descriptions()
            if callable_functions:
                new_message = stream_chat_completion(
                    engine=self.engine,
                    messages=self.full_memory(),
                    print_output=not self.ignore_none_function_messages,
                    functions=callable_functions,
                    function_call="auto",
                    **self.engine_args
                )
            else:
                new_message = stream_chat_completion(
                    engine=self.engine,
                    messages=self.full_memory(),
                    print_output=not self.ignore_none_function_messages,
                    **self.engine_args
                )

            if new_message.get("function_call"):
                self.memory.append(new_message)
                function_response = self._call_function(
                    new_message["function_call"])
                if function_response is None:
                    function_response = 'done'
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
        return self

    def last_message(self):
        """
        Retreive the last message.
        """
        return self.memory[-1]
