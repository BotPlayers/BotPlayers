import yaml
from typing import Tuple, List
from pathlib import Path
from .agent import Agent, agent_callable
from .util import parse_experience_data, markdown_bullets_to_list
from .config import DEFAULT_ENGINE

EXPERIENCE_ROOT = Path(__file__).parent / 'experience'
BOTS = dict()


def _load_bot(name: str, engine: str = DEFAULT_ENGINE) -> Tuple[Agent, str]:
    global BOTS
    if name in BOTS:
        return BOTS[name]
    raw_exp_data = yaml.safe_load(open(EXPERIENCE_ROOT / f'{name}.yaml', 'r'))
    exp_data = parse_experience_data(raw_exp_data)
    agent = Agent(
        f'bots.{name}', engine=engine,
        function_call_repeats=1,
        ignore_none_function_messages=False
    ).receive_messages(
        exp_data,
        print_output=False
    )
    template_user = raw_exp_data['template']['user']
    BOTS[name] = (agent, template_user)
    return BOTS[name]


@agent_callable()
def rephrase(sentence: str) -> str:
    """
    Rephrase a sentence.

    Args:
        sentence: the sentence to be rephrased.

    Returns:
        result: the rephrased sentence.
    """
    agent, template_user = _load_bot('rephrase')
    return agent.receive_message(
        {'role': 'user', 'content': template_user.format(input=sentence)}
    ).think_and_act().last_message()['content']


@agent_callable()
def is_related(question: str, info: str) -> bool:
    """
    Judge whether the info is related to the question.

    Args:
        question: the question.
        info: the info.

    Returns:
        result: whether the info is related to the question.
    """
    agent, template_user = _load_bot('is_related')
    return agent.receive_message(
        {'role': 'user', 'content': template_user.format(
            question=question, info=info)}
    ).think_and_act().last_message()['content'].lower().startswith('y')


@agent_callable()
def is_sufficient(question: str, info: str) -> bool:
    """
    Judge whether the info is sufficient to answer the question.

    Args:
        question: the question.
        info: the info.

    Returns:
        result: whether the info is sufficient to answer the question.
    """
    agent, template_user = _load_bot('is_sufficient')
    return agent.receive_message(
        {'role': 'user', 'content': template_user.format(
            question=question, info=info)}
    ).think_and_act().last_message()['content'].lower().startswith('y')


@agent_callable()
def is_confusing(sentence: str) -> Tuple[bool, str]:
    """
    Judge whether there are confusing references in the sentence.

    Args:
        sentence: the sentence.

    Returns:
        result: whether the sentence has confusing references.
        explanation: the explanation of the result.
    """
    agent, template_user = _load_bot('is_confusing')
    content = agent.receive_message(
        {'role': 'user', 'content': template_user.format(sentence=sentence)}
    ).think_and_act().last_message()['content']  # content should be like 'Explanation: ...\nHas confusing references: yes/no'

    assert content.count('Explanation: ') == 1
    assert content.count('Has confusing references: ') == 1

    result = content.split(
        'Has confusing references:')[-1].strip().lower().startswith('y')
    explanation = content.split('Explanation:')[-1].split(
        'Has confusing references:')[0].strip()
    return result, explanation


@agent_callable()
def summarize(info: str) -> List[str]:
    """
    Summarize the info.

    Args:
        info: the info.

    Returns:
        result: the summerized bullets of the info.
    """
    agent, template_user = _load_bot('summarize')
    bullets_in_markdown: str = agent.receive_message(
        {'role': 'user', 'content': template_user.format(info=info)}
    ).think_and_act().last_message()['content']
    return markdown_bullets_to_list(bullets_in_markdown)


@agent_callable()
def extract_info(info: str) -> List[str]:
    """
    Extract info from the info.

    Args:
        info: the info.

    Returns:
        result: the extracted info.
    """
    agent, template_user = _load_bot('extract_info')
    bullets_in_markdown = agent.receive_message(
        {'role': 'user', 'content': template_user.format(input=info)}
    ).think_and_act().last_message()['content']
    return markdown_bullets_to_list(bullets_in_markdown)


@agent_callable()
def extract_keywords(info: str) -> List[str]:
    """
    Extract keywords from the info.

    Args:
        info: the info.

    Returns:
        result: the keywords of the info.
    """
    agent, template_user = _load_bot('extract_keywords')
    bullets_in_markdown = agent.receive_message(
        {'role': 'user', 'content': template_user.format(input=info)}
    ).think_and_act().last_message()['content']
    return markdown_bullets_to_list(bullets_in_markdown)
