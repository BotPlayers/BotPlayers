import yaml
from botplayers import agent_callable, Agent, InteractiveSpace
from botplayers.util import parse_experience_data


class IsUseful:
    worker: Agent = Agent(
        'Bot.IsUseful', engine='gpt-3.5-turbo',
        function_call_repeats=1,
        ignore_none_function_messages=False
    ).receive_messages(
        parse_experience_data(yaml.safe_load(
            open('app/experiments/is_useful.yaml', 'r'))),
        print_output=False
    )

    def __call__(self, user_question: str, current_info: str):
        """
        Judge whether the current info is useful to answer the user's question.
        """
        return self.worker.receive_message(
            {'role': 'user', 'content':
             'Question: ' + user_question + '\n' +
             'Info: ' + current_info + '\n' +
             'Is this info related to the question? Answer yes or no.'}
        ).think_and_act().last_message()['content'].lower().startswith('y')


class IsSufficient:
    worker: Agent = Agent(
        'Bot.IsSufficient', engine='gpt-3.5-turbo',
        function_call_repeats=1,
        ignore_none_function_messages=False
    ).receive_messages(
        parse_experience_data(yaml.safe_load(
            open('app/experiments/is_sufficient.yaml', 'r'))),
        print_output=False
    )

    def __call__(self, user_question: str, current_info: list):
        """
        Judge whether the current info is sufficient to answer the user's question.
        """
        return self.worker.receive_message(
            {'role': 'user', 'content':
             'Question: ' + user_question + '\n' +
             'Info: ' + ' '.join(current_info) + '\n' +
             'Are these info sufficient to answer the question? Answer yes or no.'}
        ).think_and_act().last_message()['content'].lower().startswith('y')


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

    is_useful = IsUseful()
    is_sufficient = IsSufficient()

    @agent_callable()
    def find_info(self, user_question: str):
        """
        Find the information from the database that are useful to answer the user's question.

        Args:
            user_question: The user's full question.
        """
        useful_info = []
        for idx, info in enumerate(self.info_list):
            if self.is_useful(user_question, info):
                useful_info.append(info)
                if idx < len(self.info_list) - 1:
                    if self.is_sufficient(user_question, useful_info):
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
