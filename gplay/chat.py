import os
import datetime
import json
from playwright.sync_api import sync_playwright

from .util import setup_pandafan_proxy, print_in_color
from .gpt_tools import (
    gpt_callable, get_gpt_callable_function_descriptions, run_chat, run_jupyter_code,
    TOKEN_ENCODING)


def trim_text(text: str, starting_idx: int = 0, max_tokens: int = 200):
    tokens = TOKEN_ENCODING.encode(text)
    if len(tokens) > max_tokens:
        text = TOKEN_ENCODING.decode(
            tokens[starting_idx:starting_idx + max_tokens])
        if starting_idx > 0:
            text = '... ' + text
        if starting_idx + max_tokens < len(tokens):
            text = text + ' ...'
            text = '[Showing {} to {} tokens from {} tokens in total, use show_more() to see more]\n{}'.format(
                starting_idx, starting_idx + max_tokens, len(tokens), text)
        else:
            text = '[This is the end of the text]\n{}'.format(text)
    return text


@gpt_callable
def get_current_datetime():
    """Get the current date time.

    Returns:
        time: the current time.
        day: the current day.
    """
    import datetime
    return {'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'day': datetime.datetime.now().strftime("%A")}


@gpt_callable
def list_files(world: dict):
    """List all files in the workspace directory.

    Returns:
        files: the list of files.
    """
    import os
    workspace = world['workspace']
    return {'files': os.listdir(workspace)}


@gpt_callable
def run_python_code(world: dict, code: str):
    """Run a given Python code. 
    Yes! You can run any Python code here to accomplish anything you want!
    Return the value of the last expression.

    Note two things in your code, 
    * Always use the global variable `WORKSPACE` (str) in your code to access your workspace directory.
    * Always use the global variable `WORKSPACE` (str) in your code to save files.
      e.g. open(os.path.join(WORKSPACE, 'my_file.txt'), 'w').write('hello world')

    Args:
        code: The Python code to be run. 

    Returns:
        result: the value of the last expression.
    """

    print_in_color(code, 'green')
    workspace = world['workspace']
    result = run_jupyter_code(code, globals={'WORKSPACE': workspace})
    return {'result': result}


@gpt_callable
def view_text_file(world: dict, file_name: str):
    """View a text file in the workspace directory.

    Args:
        file_name: the file name.

    Returns:
        text: the text in the file.
    """
    import os
    workspace = world['workspace']
    file_path = os.path.join(workspace, file_name)
    text = open(file_path, 'r').read()
    world['last_result'] = text
    world['last_result_starting_idx'] = 0
    world['last_result_name'] = 'text'

    trimmed_text = trim_text(
        world['last_result'], world['last_result_starting_idx'])
    return {'text': trimmed_text, 'file_name': file_name}


@gpt_callable
def browse_webpage(world: dict, url: str):
    """Browse a webpage.

    Args:
        url: the url of the webpage.

    Returns:
        a11y_snapshot: the accessibility (a11y) snapshot of the current webpage.
    """
    if 'playwright' not in world:
        world['playwright'] = sync_playwright().start()
        # world['playwright'].start()
    if 'browser' not in world:
        world['browser'] = world['playwright'].chromium.launch()
    if 'page' not in world:
        world['page'] = world['browser'].new_page()

    page = world['page']
    page.goto(url)
    a11y_snapshot = page.accessibility.snapshot()

    a11y_snapshot_txt = json.dumps(a11y_snapshot, indent=2)

    world['last_result'] = a11y_snapshot_txt
    world['last_result_starting_idx'] = 0
    world['last_result_name'] = 'a11y_snapshot'

    trimmed_text = trim_text(
        world['last_result'], world['last_result_starting_idx'])
    # print_in_color(a11y_snapshot, 'green')

    return {'a11y_snapshot': trimmed_text}


@gpt_callable
def show_more_last_result(world: dict):
    """Show more content from last result.

    Returns:
        text: the text.
    """
    world['last_result_starting_idx'] += 200
    trimmed_text = trim_text(
        world['last_result'], world['last_result_starting_idx'])
    return {world['last_result_name']: trimmed_text}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pandafan', action='store_true', default=False)
    parser.add_argument('--engine', type=str, default='gpt-4')
    parser.add_argument('--workspace', type=str, default='.workspace')
    parser.add_argument('--prompt-path', type=str,
                        default='prompts/default.txt')
    parser.add_argument('--enable-code-interpreter-mode',
                        action='store_true', default=False)

    args = parser.parse_args()
    prompt = open(args.prompt_path, 'r').read()

    prompt = prompt.format(
        current_date=datetime.datetime.now().strftime('%Y-%m-%d'),
        workspace=os.path.abspath(args.workspace))

    if args.pandafan:
        setup_pandafan_proxy()

    os.makedirs(args.workspace, exist_ok=True)

    print_in_color(get_gpt_callable_function_descriptions(), 'green')

    run_chat(args.engine, system_message=prompt,
             enable_code_interpreter_mode=args.enable_code_interpreter_mode,
             world_state={'workspace': args.workspace})
