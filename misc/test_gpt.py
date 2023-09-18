import botplayers


prompt = """
You are a knight in the kingdom of Larion. You are hunting the evil dragon who has been terrorizing the kingdom. You enter the forest searching for the dragon and see something.
"""

botplayers.Agent('Bot', prompt=prompt, engine='gpt-3.5-turbo').receive_message(
    {'role': 'user', 'content': 'You see a dragon.'}).think_and_act()
