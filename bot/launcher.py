import os
import logging
import json
import asyncio
from warnings import filterwarnings
from telegram import Update
from telegram.warnings import PTBUserWarning
from telegram.error import TimedOut
from telegram.ext import Application, PicklePersistence
from telegram.request import HTTPXRequest
from concurrent.futures import ThreadPoolExecutor
import threading

from .client import AirBotClient
from handlers import AirDaoHandler

class BotLauncher:
    """Bot launcher which parses configuration file, creates and starts the bot."""

    def __init__(self, config_file_name) -> None:
        self._test = False
        self._log = self.setup_logging()
        self.config = self.load_config(config_file_name)
        

        self._client = AirBotClient(config=self.config)
        self._bot = self._client.launch_application()
        
        self.loop = asyncio.new_event_loop()  
        asyncio.set_event_loop(self.loop)
        self.tasks=set()
        
        self.max_connections = 10
        self.executor = ThreadPoolExecutor(max_workers=self.max_connections)
        self.lock = threading.Lock()          
        
    def setup_logging(self):
        filterwarnings(action="ignore", message=r".*CallbackQueryHandler", category=PTBUserWarning)
        logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        return logging.getLogger(__name__)

    def load_config(self, config_file_name):
        config = {}
        try:
            with open(f"{config_file_name}", "r") as config_file:
                config = json.load(config_file)
        except Exception as e:
            logging.error(f"Error: {e}")
            
        return config


    def _setup_handlers(self):
        self._log.info("Setting up handlers")
        self.airdao = AirDaoHandler(self._bot, self.config)
        self.conv_handler = self.airdao.create_conversation_handler()

        self._bot.add_handler(self.conv_handler)
        
        return self.airdao
      
    def run_asyncio(self, tasks):
        try:
            self._log.info(f"Running asyncio tasks: {tasks}")
            self.loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as e:
            self._log.error(f"Exception in asyncio loop: {e}")
        finally:
            self.loop.close()

    def run(self) -> None:
        """Run bot."""
        self._setup_handlers()  
        
        try:
            self._log.info("Bot is running polling now")
            self._bot.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            self._log.info("Shutting down...")
        finally:
            self._log.info("Shutting down...")
            self._bot.stop_running()
