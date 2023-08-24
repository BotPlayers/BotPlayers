from typing import List, Dict
from botplayers import agent_callable, Agent, InteractiveSpace


def to_markdown(list_data: list):
    return '\n'.join([f'- {item}' for item in list_data])


class Notebook(InteractiveSpace):
    info_len_limit = 500
    seach_info_limit = 10

    info = []
    keyword2info_ids: Dict[str, List[int]] = dict()

    @agent_callable()
    def record_info(self, info: str, keywords: str, importance: int = 0):
        f"""
        Record an important information into the notebook.

        Args:
            info: The information to be recorded. The information should be no more than {self.info_len_limit} characters.
            keywords: The keywords for the information. The keywords should be separated by commas.
            importance: The importance of the information. The importance should be an integer between 0 and 10.
        """
        if len(info) > self.info_len_limit:
            return {'result': 'fail', 'content': f'The information should be no more than {self.info_len_limit} characters.'}
        if importance < 0 or importance > 10:
            return {'result': 'fail', 'content': 'The importance should be an integer between 0 and 10.'}

        keywords = [keyword.strip().lower() for keyword in keywords.split(',')]
        self.info.append(
            {'content': info, 'keywords': keywords, 'importance': importance})
        info_id = len(self.info) - 1

        for keyword in keywords:
            if keyword not in self.keyword2info_ids:
                self.keyword2info_ids[keyword] = []
            self.keyword2info_ids[keyword].append(info_id)
        return {'result': 'success'}

    @agent_callable()
    def search_info(self, keywords: str):
        """
        Search information from notebook using keywords.

        Args:
            keywords: The keywords for the information. The keywords should be separated by commas.
        """
        keywords = [keyword.strip().lower() for keyword in keywords.split(',')]

        info_ids = []
        for keyword in keywords:
            if keyword in self.keyword2info_ids:
                info_ids.extend(self.keyword2info_ids[keyword])
        info_ids = list(set(info_ids))

        if len(info_ids) == 0:
            return {'result': 'fail', 'content': 'No information found.'}
        else:
            info_ids = sorted(
                info_ids, key=lambda info_id: self.info[info_id]['importance'], reverse=True)
            info_ids = info_ids[:self.seach_info_limit]
            return {'result': 'success', 'content': to_markdown([self.info[info_id] for info_id in info_ids])}

    @agent_callable()
    def list_keywords(self):
        """
        List all keywords in the notebook.
        """
        return {'result': 'success', 'content': to_markdown(self.keyword2info_ids.keys())}


notebook = Notebook()
agent = Agent(
    'Recorder', prompt=('You are a helpful bot. You can use functions to record and search information. '),
    engine='gpt-3.5-turbo',
    interactive_objects=[notebook],
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
        agent.receive_message({'role': 'user', 'content': user_message})
    agent.think_and_act()
