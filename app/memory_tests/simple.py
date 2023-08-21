from botplayers import agent_callable, Agent, InteractiveSpace


def to_markdown(list_data: list):
    return '\n'.join([f'- {item}' for item in list_data])


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

    @agent_callable
    def review_info(self, agent: Agent):
        """
        View the information from the database.
        You can call this function multiple times to find more useful information.
        """
        useful_info = []
        for idx, info in enumerate(self.info_list):
            if idx < len(self.info_list) - 1:
                info_show_to_agent = f"[info from database]: {info}\n" + \
                    "Is this info useful? Answer yes or no."
            else:
                info_show_to_agent = f"[info from database]: {info}\n" + \
                    "There are no more info in the dabase."

            response = agent.derive_avatar(interactive_objects=[]).receive_message(
                {'role': 'user', 'content': info_show_to_agent}
            ).think_and_act().last_message()

            if response['content'].lower().startswith('y'):
                useful_info.append(info)

                if idx < len(self.info_list) - 1:
                    response = agent.derive_avatar(interactive_objects=[]).receive_message(
                        {'role': 'user', 'content':
                         'Current info:\n' + to_markdown(useful_info) + '\n' +
                         'Do you have sufficient infomation to answer the user\'s question? Answer yes or no.'}
                    ).think_and_act().last_message()
                    
                    if response['content'].lower().startswith('y'):
                        break

        return useful_info


info_database = Database()

agent = Agent(
    'Bot', prompt=('You are a helpful bot. You can use functions to access the knowledge from a database. '
                   'Answer questions using only the knowledge from the database.'),
    engine='gpt-4',
    interactive_objects=[info_database],
    function_call_repeats=1,
    ignore_none_function_messages=False)

while True:
    user_message = input('>> ')
    if user_message in {'exit', 'q', 'quit()', 'quit'}:
        break
    if user_message == '::mem':
        agent.print_memory()
        continue
    if user_message.strip() != '':
        agent.receive_message({'role': 'user', 'content': user_message})
    agent.think_and_act()
