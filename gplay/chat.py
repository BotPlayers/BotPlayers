import os
import json
import openai

from .util import (
    gpt_callable, get_gpt_callable_function_descriptions, get_gpt_callable_function,
    setup_pandafan_proxy)


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
                print(f'[{delta["role"]}]: ', end='')

            if content == '' and 'content' in delta and delta['content'] == '\n\n':
                continue

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
                print(delta['content'], end='')

    print()
    message = dict()
    message['role'] = role
    message['content'] = content
    if len(function_call) > 0:
        print(f'function_call: {function_call}')
        message['function_call'] = function_call
    return message


def run_chat(engine: str, t: float = 1.0):
    messages = [
        {"role": "system",
         "content": ("You are a helpful assistant. When calling functions, "
                     "only use the functions you have been provided with.")},
    ]
    while True:
        user_content = input("[user]: ")
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
                # Note: the JSON response may not always be valid; be sure to handle errors
                function_name = new_message["function_call"]["name"]
                print(f'[system]: Calling function {function_name} ...')

                function_to_call: callable = get_gpt_callable_function(
                    function_name)
                function_args = new_message["function_call"]["arguments"]
                if function_args is None:
                    function_args = dict()
                else:
                    function_args: dict = json.loads(function_args)

                print(f'[system]:     with arguments {function_args}')
                function_response = function_to_call(**function_args)
                print(f'[system]: Function response: {function_response}')

                # Send the info on the function call and function response to GPT
                messages.append(new_message)
                messages.append(
                    {
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(function_response),
                    }
                )  # extend conversation with function response
            else:
                messages.append(new_message)
                break


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
