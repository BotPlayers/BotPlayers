import os
import datetime
from .util import setup_pandafan_proxy, print_in_color
from .gpt_tools import (
    gpt_callable, get_gpt_callable_function_descriptions, run_chat, run_jupyter_code)


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
    """List all files in the current directory.

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
