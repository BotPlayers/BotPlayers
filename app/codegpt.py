import os
from botplayers import agent_callable, Agent
from botplayers.util import print_in_color


def run_jupyter_code(script, globals=None, locals=None):
    '''Execute a script and return the value of the last expression'''
    import ast
    stmts = list(ast.iter_child_nodes(ast.parse(script)))
    if not stmts:
        return None
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


class Env:
    workspace: str = '.workspace'

    @agent_callable()
    def run_code(self, python_code: str):
        """Run python code.
        Yes! You can run any Python code here to accomplish anything you want!
        Return the value of the last expression.

        Args:
            python_code: the Python code to be run.

        Returns:
            result: the result of running the Python code.
        """
        print_in_color(python_code, 'green')
        prevdir = os.path.abspath(os.curdir)
        workspace = os.path.abspath(self.workspace)
        try:
            os.chdir(workspace)
            result = run_jupyter_code(python_code)
        except Exception as e:
            os.chdir(prevdir)
            raise e
        os.chdir(prevdir)
        return {'result': result}

    @agent_callable()
    def list_files(self):
        """List all files in the current directory.

        Returns:
            files: the list of files.
        """
        import os
        return {'files': os.listdir(self.workspace)}


if __name__ == '__main__':
    prompt = "You are CodeGPT. \n\n#Tools\n\n##Functions\n\nOnly call functions that you are provided with."

    env = Env()
    os.makedirs(env.workspace, exist_ok=True)

    agent = Agent('CodeGPT', prompt=prompt,
                  engine='gpt-4',
                  interactive_objects=[env],
                  function_call_repeats=10,
                  ignore_none_function_messages=False)

    while True:
        user_message = input('>> ')
        if user_message in {'exit', 'q', 'quit()', 'quit'}:
            break
        if user_message == '::mem':
            agent.print_full_memory()
            continue
        if user_message.strip() != '':
            agent.receive_message(
                {'role': 'user', 'content': user_message})
        agent.think_and_act()
