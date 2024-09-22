from pathlib import Path
from .webhook import *


webhook = Webhook.from_config_file(Path(__file__).parent / '../configs/config_staging.json')


def trade_alert(
    market_name: str,
    taker_address: str,
    size: float,
    is_yes: bool,
    percent: float,
):
    return webhook.execute(Message(
    embeds=[
        Embed(
            title='Trade Made',
            description=f'`{market_name}`',
            color=0xFFFF00,
            thumbnail=Thumbnail(
                url='https://i.imgur.com/HXMiOsT.jpeg',
            ),
            fields=[
                Field('User', f'`{taker_address}`', False),
                Field('Bet Size', f'`{size}`', True),
                Field('Side', '`YES`' if is_yes else '`NO`', True),
                Field('Odds', f'`{percent:.2f}% | {1} : {100 / percent - 1:.2f}`', True),
            ],
        ),
    ],
))

# trade_alert(
#     'Donald Trump opens a farm tomorrow',
#     '0x' + '0' * 40,
#     21.2,
#     True,
#     40.0,
# )
