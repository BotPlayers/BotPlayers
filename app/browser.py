import os
import yaml
import tiktoken
from playwright.sync_api import sync_playwright

from botplayers import Agent, agent_callable
from botplayers.util import print_in_color

TOKEN_ENCODING = tiktoken.encoding_for_model('gpt-3.5-turbo')


class Browser:
    playwright = None
    browser = None
    page = None

    last_result = None
    last_result_starting_idx = 0
    last_result_name = None

    max_visible_tokens = 300

    def setup(self):
        if self.playwright is None:
            self.playwright = sync_playwright().start()
        if self.browser is None:
            self.browser = self.playwright.chromium.launch()
        if self.page is None:
            self.page = self.browser.new_page()

    def last_result_visible_part(self):
        text = self.last_result
        tokens = TOKEN_ENCODING.encode(text)
        if len(tokens) > self.max_visible_tokens:
            text = TOKEN_ENCODING.decode(
                tokens[self.last_result_starting_idx:self.last_result_starting_idx + self.max_visible_tokens])
            if self.last_result_starting_idx > 0:
                text = '... ' + text
            if self.last_result_starting_idx + self.max_visible_tokens < len(tokens):
                text = text + ' ...'
                text = '[Showing {} to {} tokens from {} tokens in total, use show_more() to see more]\n{}'.format(
                    self.last_result_starting_idx, self.last_result_starting_idx + self.max_visible_tokens, len(tokens), text)
            else:
                text = '[This is the end of the text]\n{}'.format(text)
        print_in_color(text, 'orange')
        return text

    @agent_callable()
    def search(self, text: str):
        """
        Search something on Google.

        Args:
            text: The text to be searched.
        """
        from serpapi import GoogleSearch
        params = {
            "api_key": os.environ['SERPAPI_API_KEY'],
            "engine": "google",
            "q": text,
            "location": "Austin, Texas, United States",
            "google_domain": "google.com",
            "gl": "us",
            "hl": "en",
            "num": 1,
        }
        search = GoogleSearch(params)
        results = search.get_json()
        keys = {'title', 'link', 'snippet'}
        return {key: value for key, value in results['organic_results'][0].items() if key in keys}

    @agent_callable()
    def browse_webpage(self, url: str):
        """Browse a webpage.

        Args:
            url: the url of the webpage.

        Returns:
            a11y_snapshot: the accessibility (a11y) snapshot of the current webpage.
        """
        self.setup()

        self.page.goto(url)
        a11y_snapshot = self.page.accessibility.snapshot()

        a11y_snapshot_txt = yaml.safe_dump(
            a11y_snapshot, indent=2, allow_unicode=True)

        self.last_result = a11y_snapshot_txt
        self.last_result_starting_idx = 0
        self.last_result_name = 'a11y_snapshot'

        trimmed_text = self.last_result_visible_part()
        return {'a11y_snapshot': trimmed_text}

    @agent_callable()
    def backward_webpage(self):
        """Go back to the previous webpage.

        Returns:
            a11y_snapshot: the accessibility (a11y) snapshot of the current webpage after going back.
        """
        self.setup()

        self.page.go_back()
        a11y_snapshot = self.page.accessibility.snapshot()

        a11y_snapshot_txt = yaml.safe_dump(
            a11y_snapshot, indent=2, allow_unicode=True)

        self.last_result = a11y_snapshot_txt
        self.last_result_starting_idx = 0
        self.last_result_name = 'a11y_snapshot'

        trimmed_text = self.last_result_visible_part()
        return {'a11y_snapshot': trimmed_text}

    @agent_callable()
    def show_more(self):
        """Show more of the last result."""
        self.last_result_starting_idx += self.max_visible_tokens
        trimmed_text = self.last_result_visible_part()
        return {'a11y_snapshot': trimmed_text}


if __name__ == '__main__':
    browser = Browser()
    agent = Agent('Bot', 'You are a bot. You can browse webpages and interact with them.',
                  interactive_objects=[browser],
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
