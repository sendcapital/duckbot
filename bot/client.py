import asyncio
import logging
from typing import Iterable
from telegram import Update
from telegram.warnings import PTBUserWarning
from telegram.error import TimedOut
from telegram.ext import Application, PicklePersistence
from telegram.request import HTTPXRequest

class AirBotClient:
    
    def __init__(self, config) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.info('Initializing bot client')
        self.config = config
        self.token = self.config["telegramToken"]
    def launch_application(self) -> Application:
      self._bot = Application.builder().token(self.token).build()
      return self._bot



