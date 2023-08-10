import inspect
import re
import json
import openai

from .util import colorize_text_in_terminal, print_in_color

GPT_CALLABLE_FUNCTION_DESCRIPTIONS = []
GPT_CALLABLE_FUNCTION_TABLE = dict()


def get_gpt_callable_function_descriptions():
    """
    Get the descriptions of all GPT callable functions.
    """
    return GPT_CALLABLE_FUNCTION_DESCRIPTIONS


def is_gpt_callable_function(name: str):
    """
    Check if a function is a GPT callable function.
    """
    return name in GPT_CALLABLE_FUNCTION_TABLE


def get_gpt_callable_function(name: str):
    """
    Get the callable function by name.
    """
    return GPT_CALLABLE_FUNCTION_TABLE[name]


def gpt_callable(function: callable):
    """
    A decorator that registers a function as a callable for GPT to call.
    """
    global GPT_CALLABLE_FUNCTION_DESCRIPTIONS
    global GPT_CALLABLE_FUNCTION_TABLE

    # Get the parameters of the function
    # https://stackoverflow.com/a/25959545/1165181

    signature = inspect.signature(function)
    parameters = signature.parameters
    required_parameters = []
    for name, parameter in parameters.items():
        if parameter.default is inspect.Parameter.empty:
            required_parameters.append(name)

    # Get the type of each parameter by parsing the signature
    # https://stackoverflow.com/a/25959545/1165181
    json_schema_types = dict()
    type_annotation_to_json_schema_type = {
        str: 'string',
        int: 'integer',
        float: 'number',
        bool: 'boolean',
    }
    for name, parameter in parameters.items():
        if parameter.annotation is not inspect.Parameter.empty:
            type_annotation = parameter.annotation
            json_schema_types[name] = type_annotation_to_json_schema_type.get(
                type_annotation, 'string')

    # Get the description of each parameter by parsing the doc
    # https://stackoverflow.com/a/10079854/1165181

    doc = function.__doc__
    if doc is None:
        doc = ''
    parameter_descriptions = {}
    for name in parameters:
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
    GPT_CALLABLE_FUNCTION_DESCRIPTIONS.append({
        'name': function.__name__,
        'description': function_description,
        'parameters': {
            'type': 'object',
            'properties': {
                name: {
                    'type': json_schema_types.get(name, 'string'),
                    'description': parameter_descriptions.get(name, ''),
                } for name in parameters
            },
            'required': required_parameters,
        },
    })
    GPT_CALLABLE_FUNCTION_TABLE[function.__name__] = function

    return function


def stream_chat_completion(engine: str, messages: list, temperature: float,
                           **kwargs):
    resp = openai.ChatCompletion.create(
        model=engine,
        messages=messages, temperature=temperature,
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
                print_in_color(delta['content'], 'yellow', end='')

    if len(content) > 0:
        print()

    message = dict()
    message['role'] = role
    message['content'] = content
    if len(function_call) > 0:
        message['function_call'] = function_call
    return message


def call_gpt_function(function_call: dict):
    # Call the function
    # Note: the JSON response may not always be valid; be sure to handle errors
    function_name = function_call["name"]

    if not is_gpt_callable_function(function_name):
        return {'error': f'"{function_name}" is not a callable function.'}

    try:
        print_in_color(f'    Calling function {function_name} ...', 'blue')
        function_to_call: callable = get_gpt_callable_function(
            function_name)

        function_args = function_call["arguments"]
        if function_args is None:
            function_args = dict()
        else:
            function_args: dict = json.loads(function_args)

        print_in_color(f'        with arguments {function_args}', 'blue')
        function_response = function_to_call(**function_args)
        print_in_color(f'        response: {function_response}', 'blue')

        return function_response
    except Exception as e:
        print_in_color(f'        error: {e}', 'red')
        return {'error': str(e)}


DEFAULT_SYSTEM_MESSAGE = ("You are a helpful assistant. When calling functions, "
                          "only use the functions you have been provided with.")


def run_chat(engine: str, t: float = 1.0, 
             system_message: str = DEFAULT_SYSTEM_MESSAGE,
             ):
    messages = [
        {"role": "system",  "content": system_message},
    ]
    while True:
        user_content = input(colorize_text_in_terminal("> ", "yellow"))
        if user_content == 'q':
            break
        messages.append({"role": "user", "content": user_content})

        while True:
            new_message = stream_chat_completion(
                engine=engine,
                messages=messages,
                temperature=t,
                functions=get_gpt_callable_function_descriptions(),
                function_call="auto",  # auto is default, but we'll be explicit
            )

            # Check if GPT wanted to call a function
            if new_message.get("function_call"):
                # Call the function
                function_response = call_gpt_function(
                    new_message["function_call"])

                # Send the info on the function call and function response to GPT
                messages.append(new_message)
                messages.append(
                    {
                        "role": "function",
                        "name": new_message["function_call"]["name"],
                        "content": json.dumps(function_response, default=str),
                    }
                )  # extend conversation with function response
            else:
                messages.append(new_message)
                break


def run_chat_with_python_call(engine:str, t:float=1.0,
                              system_message:str = DEFAULT_SYSTEM_MESSAGE,
                              ):
    messages = [
        {"role": "system",  "content": system_message},
    ]
    while True:
        user_content = input(colorize_text_in_terminal("> ", "yellow"))
        if user_content == 'q':
            break
        messages.append({"role": "user", "content": user_content})

        while True:
            new_message = stream_chat_completion(
                engine=engine,
                messages=messages,
                temperature=t,
                stop=["\n```Python\n", "\n```python\n", "\n```py\n", "\n```Py\n"],
            )

            if new_message['content'].endswith("\n```"):
                # Remove the trailing ``` from the message
                new_message['content'] = new_message['content'][:-3]

                # Remove the leading ``` from the message
                new_message['content'] = new_message['content'][5:]

                # Send the info on the function call and function response to GPT
                messages.append(new_message)
                messages.append(
                    {
                        "role": "python",
                        "content": new_message['content'],
                    }
                )
                break

            # Check if GPT wanted to call a function
            if new_message.get("function_call"):
                # Call the function
                function_response = call_gpt_function(
                    new_message["function_call"])

                # Send the info on the function call and function response to GPT
                messages.append(new_message)
                messages.append(
                    {
                        "role": "function",
                        "name": new_message["function_call"]["name"],
                        "content": json.dumps(function_response, default=str),
                    }
                )
