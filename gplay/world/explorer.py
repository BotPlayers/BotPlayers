import yaml
from playwright.sync_api import sync_playwright

from .world import World
from ..agent import agent_callable, TOKEN_ENCODING
from ..util import read_prompt, print_in_color


class Explorer(World):
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
    def get_selector_from_a11y_node_name(self, a11y_node_name:str):
        """Get the selector of a webpage element from its accessibility (a11y) node name.

        Args:
            a11y_node_name: the accessibility (a11y) node name of the element.

        Returns:
            selector: the selector of the element.
        """
        self.setup()

        selector = self.page.query_selector(a11y_node_name)
        if selector is None:
            raise Exception(f'Could not find a selector for the a11y node name "{a11y_node_name}"')
        return selector._selector

    @agent_callable()
    def click_on_webpage(self, selector: str):
        """Click on a webpage element.

        Args:
            selector: the selector of the element to click.

        Returns:
            a11y_snapshot: the accessibility (a11y) snapshot of the current webpage after clicking.
        """
        self.setup()

        self.page.click(selector)
        a11y_snapshot = self.page.accessibility.snapshot()

        a11y_snapshot_txt = yaml.safe_dump(
            a11y_snapshot, indent=2, allow_unicode=True)

        self.last_result = a11y_snapshot_txt
        self.last_result_starting_idx = 0
        self.last_result_name = 'a11y_snapshot'

        trimmed_text = self.last_result_visible_part()
        return {'a11y_snapshot': trimmed_text}

    @agent_callable()
    def type_on_webpage(self, selector: str, text: str):
        """Type on a webpage element.

        Args:
            selector: the selector of the element to type on.
            text: the text to type.

        Returns:
            a11y_snapshot: the accessibility (a11y) snapshot of the current webpage after typing.
        """
        self.setup()

        self.page.fill(selector, text)
        a11y_snapshot = self.page.accessibility.snapshot()

        a11y_snapshot_txt = yaml.safe_dump(
            a11y_snapshot, indent=2, allow_unicode=True)

        self.last_result = a11y_snapshot_txt
        self.last_result_starting_idx = 0
        self.last_result_name = 'a11y_snapshot'

        trimmed_text = self.last_result_visible_part()
        return {'a11y_snapshot': trimmed_text}

    @agent_callable()
    def type_on_webpage_and_press_enter(self, selector: str, text: str):
        """Type on a webpage element and press enter.

        Args:
            selector: the selector of the element to type on.
            text: the text to type.

        Returns:
            a11y_snapshot: the accessibility (a11y) snapshot of the current webpage after typing.
        """
        self.setup()

        self.page.fill(selector, text)
        self.page.press(selector, 'Enter')
        a11y_snapshot = self.page.accessibility.snapshot()

        a11y_snapshot_txt = yaml.safe_dump(
            a11y_snapshot, indent=2, allow_unicode=True)

        self.last_result = a11y_snapshot_txt
        self.last_result_starting_idx = 0
        self.last_result_name = 'a11y_snapshot'

        trimmed_text = self.last_result_visible_part()
        return {'a11y_snapshot': trimmed_text}

    @agent_callable()
    def scroll_to_webpage(self, selector: str):
        """Scroll to a webpage element.

        Args:
            selector: the selector of the element to scroll to.

        Returns:
            a11y_snapshot: the accessibility (a11y) snapshot of the current webpage after scrolling.
        """
        self.setup()

        self.page.scroll_to(selector)
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

    def run(self):
        while True:
            user_message = input('>> ')
            if user_message in {'exit', 'q', 'quit()', 'quit'}:
                break
            if user_message.strip() != '':
                for agent in self.agents.values():
                    agent.receive_message(
                        {'role': 'user', 'content': user_message})

            agents = list(self.agents.values())
            for agent in agents:
                agent.think_and_act_in_world(self)


if __name__ == '__main__':
    explorer = Explorer()
    explorer.add_agent(
        'bot', 'You are a bot. You can browse webpages and interact with them.',
        function_call_repeats=10,
        ignore_none_function_messages=False)
    explorer.run()
