import json
import logging
from typing import Self
import requests
from dataclasses import dataclass, asdict


@dataclass
class Footer:
    text: str  # footer text | 2048 characters


@dataclass
class Image:
    url: str  # source url of image (only supports http(s) and attachments)
    proxy_url: int | None = None  # a proxied url of the image
    height: int | None = None  # height of image
    width: int | None = None  # width of image


@dataclass
class Author:
    name: str  # name of author | 256 characters


@dataclass
class Field:
    name: str  # name of the field | 256 characters
    value: str  # value of the field | 1024 characters
    inline: bool  # whether or not this field should display inline


@dataclass
class Embed:
    title: str | None = None  # title of embed | 256 characters
    description: str | None = None  # description of embed | 4096 characters
    color: int | None = None  # color code of the embed
    footer: Footer | None = None  # footer information
    image: Image | None = None  # image information
    author: Author | None = None  # author information
    fields: list[Field] | None = None  # fields information, max of 25


@dataclass
class Message:
    '''
    required: one of `content`, `file`, `embeds`, `poll`
    the combined sum of characters in all `title`, `description`, `field.name`, `field.value`, `footer.text`, and `author.name` fields across all embeds attached to a message must not exceed 6000 characterss. Violating any of these constraints will result in a `Bad Request` response.
    Embeds are deduplicated by URL. If a message contains multiple embeds with the same URL, only the first is shown.
    '''
    content: str | None = None  # the message contents (up to 2000 characters)
    username: str | None = None  # override the default username of the webhook
    embeds: list[Embed] | None = None  # embedded `rich` content


@dataclass
class Webhook:
    id: str
    token: str
    DISCORD_URL: str = 'https://discord.com/api'

    @classmethod
    def from_config_file(cls, file_path: str) -> Self:
        try:
            with open(file_path, 'r') as config_file:
                discord_config = json.load(config_file)['discord_webhook']
            return cls(discord_config['id'], discord_config['token'])
        except Exception as e:
            logging.error(f"Error: {e}")
    
    def execute(self, data: Message, wait: bool = False) -> requests.Response:
        return requests.post(f'{self.DISCORD_URL}/webhooks/{self.id}/{self.token}?wait={wait}', json=asdict(data))
