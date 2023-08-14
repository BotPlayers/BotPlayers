import os


def setup_pandafan_proxy():
    os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10080'
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10080'


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
