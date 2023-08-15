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
                body=stmts[:-1], type_ignores=[]),
                filename="<ast>", mode="exec"), globals, locals)
        # then we eval the last one
        return eval(compile(ast.Expression(body=stmts[-1].value),
                            filename="<ast>", mode="eval"), globals, locals)
    else:
        # otherwise we just execute the entire code
        return exec(script, globals, locals)
