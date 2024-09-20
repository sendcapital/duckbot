import argparse
import logging

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def process_args():
    """
    Get start/end datetime arguments and return useful variables
    :rtype: tuple of options
    """
    config_file_name = None
    
    parser = argparse.ArgumentParser(
        description='AirDao Processing argument parser')

    parser.add_argument('-c', '--config-file', action="store", type=str, required=True)

    args = parser.parse_args()

    config_file_name = args.config_file

    return config_file_name



