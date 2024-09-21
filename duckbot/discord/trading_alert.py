from .webhook import *


webhook = Webhook.from_config_file('configs/config_staging')
webhook.execute(Message(
    'test',
))
