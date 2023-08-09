from .util import setup_pandafan_proxy, print_in_color
from .gpt_tools import gpt_callable, get_gpt_callable_function_descriptions, run_chat


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
def run_python_code(code: str):
    """Run a given Python code. 
    Yes! You can run any Python code here to accomplish anything you want!
    Return the value of the last expression.

    Args:
        code: The Python code to be run.

    Returns:
        result: the value of the last expression.
    """
    code_lines = code.split('\n')
    code_lines = [line for line in code_lines if len(line.strip()) > 0]
    if len(code_lines) == 0:
        return {'error': 'No code to run.'}
    exec('\n'.join(code_lines[:-1]))
    return {'result': eval(code_lines[-1])}


@gpt_callable
def list_files():
    """List all files in the current directory.

    Returns:
        files: the list of files.
    """
    import os
    return {'files': os.listdir('.')}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--pandafan', action='store_true', default=False)
    parser.add_argument('--t', type=float, default=1.0)
    parser.add_argument('--engine', type=str, default='gpt-4')
    parser.add_argument('--workspace', type=str, default='.workspace')

    args = parser.parse_args()

    if args.pandafan:
        setup_pandafan_proxy()

    import os
    os.makedirs(args.workspace, exist_ok=True)
    os.chdir(args.workspace)
    print_in_color(f'Working directory: {os.getcwd()}', 'blue')

    print_in_color(get_gpt_callable_function_descriptions(), 'green')

    run_chat(args.engine, args.t,
             system_message=('You are the Python chatbot! '
                             'You can run any Python code using run_python_code '
                             'to accomplish anything the user wants!'))
