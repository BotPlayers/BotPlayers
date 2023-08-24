import yaml
from botplayers import agent_callable, Agent, InteractiveSpace
from botplayers.function import is_related, is_sufficient


class Database(InteractiveSpace):
    info_list = [
        'Alice is born in 1990.',
        'Bob is born in 1991.',
        'David is born in 1995.',
        'Alice is in Kansas.',
        'Bob is in New York.',
        'David is in California.',
        'Alice likes David.'
    ]

    # is_useful = IsUseful()
    # is_sufficient = IsSufficient()

    @agent_callable()
    def find_info(self, user_question: str):
        """
        Find the information from the database that are useful to answer the user's question.

        Args:
            user_question: The user's full question.
        """
        useful_info = []
        for idx, info in enumerate(self.info_list):
            if is_related(user_question, info):
                useful_info.append(info)
                if idx < len(self.info_list) - 1:
                    if is_sufficient(user_question, useful_info):
                        break
        return useful_info


info_database = Database()

agent = Agent(
    'Bot', prompt=('You are a helpful bot. You can use functions to access the knowledge from a database. '
                   'Answer questions using only the knowledge from the database.'),
    engine='gpt-3.5-turbo',
    interactive_objects=[info_database],
    function_call_repeats=1,
    ignore_none_function_messages=False)

while True:
    user_message = input('>> ')
    if user_message in {'exit', 'q', 'quit()', 'quit'}:
        break
    if user_message == '::mem':
        agent.print_full_memory()
        continue
    if user_message.strip() != '':
        agent.receive_message({'role': 'user', 'content': user_message})
    agent.think_and_act()
