import inspect
import re
import json
import openai

from .util import print_in_color

WORLD_PARAM_NAME = 'world'

GPT_CALLABLE_FUNCTION_DESCRIPTIONS = []
GPT_CALLABLE_FUNCTION_TABLE = dict()


def get_gpt_callable_function_descriptions():
    """
    Get the descriptions of all GPT callable functions.
    """
    return GPT_CALLABLE_FUNCTION_DESCRIPTIONS


def gpt_callable(function: callable):
    """
    A decorator that registers a function as a callable for GPT to call.
    """
    global GPT_CALLABLE_FUNCTION_DESCRIPTIONS
    global GPT_CALLABLE_FUNCTION_TABLE

    # Get the parameters of the function
    signature = inspect.signature(function)
    parameters = signature.parameters
    has_world_param = WORLD_PARAM_NAME in parameters
    parameters_wo_world = {
        name: parameter for name, parameter in parameters.items()
        if name != WORLD_PARAM_NAME}

    required_parameters = []
    for name, parameter in parameters_wo_world.items():
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
    for name, parameter in parameters_wo_world.items():
        if parameter.annotation is not inspect.Parameter.empty:
            type_annotation = parameter.annotation
            json_schema_types[name] = type_annotation_to_json_schema_type.get(
                type_annotation, 'string')

    # Get the description of each parameter by parsing the doc
    doc = function.__doc__
    if doc is None:
        doc = ''
    parameter_descriptions = {}
    for name in parameters_wo_world:
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
                } for name in parameters_wo_world
            },
            'required': required_parameters,
        },
    })
    GPT_CALLABLE_FUNCTION_TABLE[function.__name__] = (
        function, has_world_param)

    return function


def stream_chat_completion(engine: str, messages: list,
                           **kwargs):
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
                print_in_color(delta['content'], 'yellow', end='')

    if len(content) > 0:
        print()

    message = dict()
    message['role'] = role
    message['content'] = content
    if len(function_call) > 0:
        message['function_call'] = function_call
    return message


def call_gpt_function(function_call: dict, world_state: dict = dict()):
    # Call the function
    # Note: the JSON response may not always be valid; be sure to handle errors
    function_name = function_call["name"]

    if function_name not in GPT_CALLABLE_FUNCTION_TABLE:
        return {'error': f'"{function_name}" is not a callable function.'}

    try:
        print_in_color(f'    Calling function {function_name} ...', 'blue')
        function_to_call, has_world_param = GPT_CALLABLE_FUNCTION_TABLE[function_name]

        function_args = function_call["arguments"]
        if function_args is None:
            function_args = dict()
        else:
            function_args: dict = json.loads(function_args)

        print_in_color(f'        with arguments {function_args}', 'blue')
        if has_world_param:
            function_args[WORLD_PARAM_NAME] = world_state
        function_response = function_to_call(**function_args)
        print_in_color(f'        response: {function_response}', 'blue')

        return function_response
    except Exception as e:
        print_in_color(f'        error: {e}', 'red')
        return {'error': str(e)}


PYTHON_CODE_BLOCK_PREFIX = '```python\n'
PYTHON_CODE_BLOCK_SUFFIX = '\n```\n'


def run_jupyter_code(script, globals=None, locals=None):
    '''Execute a script and return the value of the last expression'''
    import ast
    stmts = list(ast.iter_child_nodes(ast.parse(script)))
    if not stmts:
        return None
    # print(stmts[-1].__dict__)
    if isinstance(stmts[-1], ast.Expr):
        # the last one is an expression and we will try to return the results
        # so we first execute the previous statements
        if len(stmts) > 1:
            exec(compile(ast.Module(
                body=stmts[:-1], type_ignores=[]), filename="<ast>", mode="exec"), globals, locals)
        # then we eval the last one
        return eval(compile(ast.Expression(body=stmts[-1].value), filename="<ast>", mode="eval"), globals, locals)
    else:
        # otherwise we just execute the entire code
        return exec(script, globals, locals)


def run_chat(engine: str,
             system_message: str,
             enable_code_interpreter_mode: bool = False,
             engine_args: dict = dict(),
             world_state: dict = dict()):

    messages = [
        {"role": "system",  "content": system_message},
    ]

    if enable_code_interpreter_mode:
        print_in_color('Code interpreter mode enabled.', 'yellow')
        engine_args['stop'] = [PYTHON_CODE_BLOCK_SUFFIX]

    while True:
        user_content = input(">> ")
        if user_content == 'q':
            break
        messages.append({"role": "user", "content": user_content})

        while True:
            if GPT_CALLABLE_FUNCTION_DESCRIPTIONS:
                new_message = stream_chat_completion(
                    engine=engine,
                    messages=messages,
                    functions=GPT_CALLABLE_FUNCTION_DESCRIPTIONS,
                    function_call="auto",  # auto is default, but we'll be explicit
                    **engine_args
                )
            else:
                new_message = stream_chat_completion(
                    engine=engine,
                    messages=messages,
                    **engine_args
                )

            if enable_code_interpreter_mode and \
                    PYTHON_CODE_BLOCK_PREFIX in new_message['content']:

                new_message['content'] += PYTHON_CODE_BLOCK_SUFFIX
                print_in_color(PYTHON_CODE_BLOCK_SUFFIX, 'yellow', end='')

                python_code_block = new_message['content'].split(
                    PYTHON_CODE_BLOCK_PREFIX)[-1].split(PYTHON_CODE_BLOCK_SUFFIX)[0]

                print_in_color(f'    Running python code block ...', 'blue')
                print_in_color(f'{python_code_block}', 'green')

                # Run the python code block like in IPython or Jupyter
                # Retreive the output of the code block
                try:
                    python_code_block_output = run_jupyter_code(
                        python_code_block)
                except Exception as e:
                    python_code_block_output = e

                print_in_color(
                    f'    Output: \n```\n{python_code_block_output}\n```', 'blue')
            else:
                python_code_block_output = None

            messages.append(new_message)

            if python_code_block_output is not None:
                messages.append(
                    {
                        "role": "system",
                        "content": f"```\n{python_code_block_output}\n```"
                    }
                )

            # Check if GPT wanted to call a function
            if new_message.get("function_call"):
                # Call the function
                function_response = call_gpt_function(
                    new_message["function_call"], world_state=world_state)

                # Send the info on the function call and function response to GPT
                messages.append(
                    {
                        "role": "function",
                        "name": new_message["function_call"]["name"],
                        "content": json.dumps(function_response, default=str),
                    }
                )  # extend conversation with function response
            else:
                break
