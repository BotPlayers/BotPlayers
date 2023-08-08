import os
import inspect
import re


def setup_pandafan_proxy():
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10080'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10080'


GPT_CALLABLE_FUNCTION_DESCRIPTIONS = []
GPT_CALLABLE_FUNCTION_TABLE = dict()


def get_gpt_callable_function_descriptions():
    """
    Get the descriptions of all GPT callable functions.
    """
    return GPT_CALLABLE_FUNCTION_DESCRIPTIONS


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

    # Register the function
    GPT_CALLABLE_FUNCTION_DESCRIPTIONS.append({
        'name': function.__name__,
        'description': function.__doc__.split('\n\n')[0],
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
