import openai
from typing import List
import numpy as np
from .util import print_in_color


def stream_chat_completion(engine: str, messages: List[dict], print_output: bool = True,
                           **kwargs) -> dict:
    """Stream chat completion.

    Args:
        engine: The engine to be used.
        messages: The messages to be sent.
        print_output: Whether to print the output.
        kwargs: Other arguments.
    """
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


def get_text_embeddings(engine: str, texts: List[str], **kwargs):
    """ Get text embeddings.

    Args:
        engine: The engine to be used.
        texts: The texts to be embedded.
    """
    assert isinstance(texts, list)
    resp = openai.Embedding.create(
        input=[text.replace("\n", "") for text in texts], model=engine,
        **kwargs
    )
    embeddings = [None] * len(texts)
    for d in resp['data']:
        embeddings[d['index']] = d['embedding']
    return np.array(embeddings)


if __name__ == '__main__':
    print(get_text_embeddings('text-embedding-ada-002',
          ['Hello world!', 'How are you doing?']))
