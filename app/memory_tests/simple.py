from botplayers import agent_callable, Agent


class Database:
    info_list = [
        'Alice is born in 1990.',
        'Bob is born in 1991.',
        'David is born in 1995.',
        'Alice is in Kansas.',
        'Bob is in New York.',
        'David is in California.',
        'Alice likes David.'
    ]

    @agent_callable()
    def review_info(self, agent: Agent):
        """
        View the information from the database.
        You can call this function multiple times to find more useful information.
        """
        for idx, info in enumerate(self.info_list):
            if idx < len(self.info_list) - 1:
                info_show_to_agent = f"[info from database]: {info}\n" + \
                    "Is this info useful? Answer yes or no."
            else:
                info_show_to_agent = f"[info from database]: {info}\n" + \
                    "There are no more info in the dabase."
            response = agent.response_to_message(
                {'role': 'user', 'content': info_show_to_agent})

            if response['content'].lower().startswith('y'):
                agent.receive_message(
                    {'role': 'user', 'content': f'Info from database: {info}'})

                if idx < len(self.info_list) - 1:
                    response = agent.response_to_message(
                        {'role': 'user', 'content':
                         'Do you have sufficient infomation to answer the user\'s question? Answer yes or no.'})
                    if response['content'].lower().startswith('y'):
                        break


info_database = Database()

agent = Agent(
    'Bot', prompt=('You are a helpful bot. You can use functions to access the knowledge from a database. '
                   'Answer questions using only the knowledge from the database.'),
    engine='gpt-3.5-turbo', function_call_repeats=1, ignore_none_function_messages=False)

while True:
    user_message = input('>> ')
    if user_message in {'exit', 'q', 'quit()', 'quit'}:
        break
    if user_message == '::mem':
        agent.print_memory()
        continue
    if user_message.strip() != '':
        agent.receive_message({'role': 'user', 'content': user_message})
    agent.think_and_act(info_database)
