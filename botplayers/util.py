import sys
from typing import List
import tiktoken


def colorize_text_in_terminal(text: str, color: str):
    """Colorize text in terminal.

    Args:
        text: The text to be colorized.
        color: The color to be used.

    Returns:
        colorized_text: The colorized text.
    """
    if color == 'red':
        return f'\033[91m{text}\033[0m'
    elif color == 'green':
        return f'\033[92m{text}\033[0m'
    elif color == 'yellow':
        return f'\033[93m{text}\033[0m'
    elif color == 'blue':
        return f'\033[94m{text}\033[0m'
    elif color == 'magenta':
        return f'\033[95m{text}\033[0m'
    elif color == 'cyan':
        return f'\033[96m{text}\033[0m'
    elif color == 'gray':
        return f'\033[90m{text}\033[0m'
    elif color == 'orange':
        return f'\033[38;5;208m{text}\033[0m'
    elif color == 'white':
        return f'\033[97m{text}\033[0m'
    elif color == 'bold':
        return f'\033[1m{text}\033[0m'
    elif color == 'underline':
        return f'\033[4m{text}\033[0m'
    elif color == 'invert':
        return f'\033[7m{text}\033[0m'
    else:
        return text


def print_in_color(text: str, color: str, end='\n'):
    """Print text in color.

    Args:
        text: The text to be printed.
        color: The color to be used.
    """
    print(colorize_text_in_terminal(text, color), end=end)


def markdown_bullets_to_list(text: str) -> List[str]:
    """Convert markdown bullets to a list.

    Args:
        text: The text to be converted.

    Returns:
        items: The list of items.
    """
    text = text.strip()
    if text == '':
        return []
    if not text.startswith('- ') and not text.startswith('* '):
        text = '- ' + text
    items = []
    for item in text.split('\n'):
        item = item.strip()
        if item.startswith('- ') or item.startswith('* '):
            items.append(item[2:])
        else:
            items[-1] += item
    return items


def parse_experience_data(data: dict, prepend_system_message: bool = True) -> List[dict]:
    """Parse experience data.

    Args:
        data: The data to be parsed.
        prepend_system_message: Whether to prepend a system message.
    """
    template = data['template']
    if prepend_system_message:
        msgs = [{'role': 'system', 'content': data['system']}]
    else:
        msgs = []
    for item in data['items']:
        for role, content in template.items():
            msgs.append({'role': role, 'content': content.format(**item)})
    return msgs


def count_message_tokens(messages: List[dict], model: str) -> int:
    """
    Function to count the number of tokens in a list of messages.

    Args:
        messages (List[dict]): The list of messages to count the tokens for.
        model (str): The model to count the tokens for.

    Raises:
        KeyError: If the model is not found.

    Returns:
        int: The number of tokens in the messages.
    """
    try:
        default_tokens_per_message = 4
        model_token_per_message_dict = {"gpt-3.5-turbo-0301": 4, "gpt-4-0314": 3, "gpt-3.5-turbo": 4, "gpt-4": 3,
                                        "gpt-3.5-turbo-16k": 4, "gpt-4-32k": 3, "gpt-4-32k-0314": 3,
                                        "models/chat-bison-001": 4}
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.", file=sys.stderr)
        encoding = tiktoken.get_encoding("cl100k_base")

    if model in model_token_per_message_dict.keys():
        tokens_per_message = model_token_per_message_dict[model]
    else:
        tokens_per_message = default_tokens_per_message

    if tokens_per_message is None:
        raise NotImplementedError(
            f"num_tokens_from_messages() is not implemented for model {model}.\n"
            " See https://github.com/openai/openai-python/blob/main/chatml.md for"
            " information on how messages are converted to tokens."
        )

    num_tokens = 0
    for message in messages:
        if isinstance(message, str):
            message = {'content': message}
        num_tokens += tokens_per_message
        num_tokens += len(encoding.encode(message['content']))

    num_tokens += 3
    return num_tokens
