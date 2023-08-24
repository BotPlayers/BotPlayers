from typing import Dict
from botplayers import agent_callable, InteractiveSpace, Agent


def read_prompt(prompt_file, **args):
    with open(prompt_file, 'r') as f:
        content = f.read()
        return content.format(**args)


class ChatRoom(InteractiveSpace):
    agents: Dict[str, Agent] = dict()

    @agent_callable()
    def get_person_names_in_this_room(self):
        """Get the names of all persons in this room.

        Returns:
            names: the list of names.
        """
        names = [agent.name for agent in self.agents.values()]
        return {'names': names}

    @agent_callable()
    def say_to_everyone(self, agent_name: str, content: str):
        """Say something to everyone in this room.

        Args:
            content: the content to say.
        """
        for name, agent in self.agents.items():
            if name != agent_name:
                agent.receive_message(
                    {'role': 'user', 'content': f'[{agent_name} says in public]: {content}'})
        return '[everyone might heard what you say]'

    @agent_callable()
    def say_to_person(self, agent_name: str, person_name: str, content: str):
        """Say something to a person in this room privately.

        Args:
            person_name: the name of the person to say to. you can't talk to the manager in private.
            content: the content to say.
        """
        if person_name not in self.agents:
            return f'[{person_name} is not in this room]'
        if agent_name == person_name:
            return f'[{person_name} is yourself]'
        self.agents[person_name].receive_message(
            {'role': 'user', 'content': f'[{agent_name} says to you in private]: {content}'})
        return f'[{person_name} might heard what you say]'

    @agent_callable()
    def logout(self, agent_name: str):
        """Logout from this chat room.

        Args:
            agent_name: the name of the agent to logout.
        """
        self.agents.pop(agent_name)
        return f'[{agent_name} has left the chat room]'

    def someone_say_to_everyone(self, content: str):
        """Say something to everyone in this room.

        Args:
            content: the content to say.
        """
        content = f'[Someone says in public]: {content}'
        for _, agent in self.agents.items():
            agent.receive_message({'role': 'user', 'content': content})


if __name__ == '__main__':
    room = ChatRoom()
    agents = [
        Agent('Alice', read_prompt('prompts/role.txt',
                                   name='Alice', age='25', location='Kansas',
                                   more_info="You don't like Bob. But you like David. You want to talk to David.",
                                   likes='Reading', dislikes='None'),
              engine='gpt-3.5-turbo',
              interactive_objects=[room],
              function_call_repeats=1,
              ignore_none_function_messages=True),
        Agent('Bob', read_prompt('prompts/role.txt',
                                 name='Bob', age='25', location='California',
                                 more_info="You like Alice. You want to talk to Alice.",
                                 likes='Play games', dislikes='None'),
              engine='gpt-3.5-turbo',
              interactive_objects=[room],
              function_call_repeats=1,
              ignore_none_function_messages=True),
        Agent('David', read_prompt('prompts/role.txt',
                                   name='David', age='25', location='Los Angeles',
                                   more_info="You don't like Alice. You are geeky.",
                                   likes='Working', dislikes='None'),
              engine='gpt-3.5-turbo',
              interactive_objects=[room],
              function_call_repeats=1,
              ignore_none_function_messages=True),
    ]

    for agent in agents:
        room.agents[agent.name] = agent

    while True:
        user_message = input('>> ')
        if user_message in {'exit', 'q', 'quit()', 'quit'}:
            break
        if user_message.strip() != '':
            room.someone_say_to_everyone(user_message)
        agents = list(room.agents.values())
        for agent in agents:
            agent.think_and_act()
