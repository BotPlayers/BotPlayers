from abc import abstractmethod
from ..agent import Agent


class World:
    agents: dict[str, Agent] = dict()

    def add_agent(self, name: str, prompt: str,
                  role: str = 'agent',
                  engine: str = 'gpt-3.5-turbo-16k',
                  function_call_repeats: int = 1,
                  ignore_none_function_messages: bool = True):
        agent = Agent(name, prompt, role=role, engine=engine,
                      function_call_repeats=function_call_repeats,
                      ignore_none_function_messages=ignore_none_function_messages)
        self.agents[name] = agent

    @abstractmethod
    def run(self):
        raise NotImplementedError()