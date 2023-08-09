import os
import json


from .util import setup_pandafan_proxy
from .gpt_tools import gpt_callable, run_chat


@gpt_callable
def calculator(expression: str):
    """Calculate the result of a given expression. 
    Note that only Python expressions are supported.

    Args:
        expression: The expression to be calculated.

    Returns:
        result: the result of the calculation.
    """
    return {'result': eval(expression)}


@gpt_callable
def get_current_datetime():
    """Get the current date time.

    Returns:
        time: the current time.
    """
    import datetime
    return {'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'day': datetime.datetime.now().strftime("%A")}


GPT_MEMORY = dict()


@gpt_callable
def store_in_memory(key: str, value: str):
    """Store any string value into memory.

    Args:
        key: The key of the value to be stored.
        value: The value to be stored.

    Returns:
        success: True if the value is successfully stored.
    """
    global GPT_MEMORY
    GPT_MEMORY[key] = value
    return {'success': True}


@gpt_callable
def get_from_memory(key: str):
    """Get the value from memory.

    Args:
        key: The key of the value to be retrieved.

    Returns:
        value: The value retrieved.
    """
    global GPT_MEMORY
    return {'value': GPT_MEMORY.get(key, None)}


@gpt_callable
def list_keys_in_memory():
    """List all keys in memory.

    Returns:
        keys: The keys in memory.
    """
    global GPT_MEMORY
    return {'keys': list(GPT_MEMORY.keys())}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pandafan', action='store_true', default=False)
    parser.add_argument('--t', type=float, default=1.0)
    parser.add_argument('--engine', type=str, default='gpt-4')
    parser.add_argument('--memory', type=str, default=None)
    args = parser.parse_args()

    if args.pandafan:
        setup_pandafan_proxy()

    # Load memory
    if args.memory is not None and os.path.exists(args.memory):
        with open(args.memory, 'r') as f:
            GPT_MEMORY = json.load(f)

    run_chat(args.engine, args.t)

    # Save memory
    if args.memory is not None:
        with open(args.memory, 'w') as f:
            json.dump(GPT_MEMORY, f)
