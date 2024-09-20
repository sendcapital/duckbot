#!/usr/bin/env python3
"""Bot Launcher Module."""
from bot import BotLauncher, setup_logging
from utils import process_args

def main() -> None:
    config_file_name = process_args()
  
    setup_logging()
    bot_launcher = BotLauncher(config_file_name)
    bot_launcher.run()  

if __name__ == '__main__':
  main()
