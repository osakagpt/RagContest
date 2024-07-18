from logging import getLogger, FileHandler, Formatter, DEBUG
import os


def setup_logger():
    # Define the directory where you want to save the log file
    log_directory = "logs"

    # Ensure the directory exists
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    # Define the full path for the log file
    log_file_path = os.path.join(log_directory, "rag_contest.log")

    # Create a file handler
    file_handler = FileHandler(log_file_path)
    file_handler.setLevel(DEBUG)

    # Create a formatter and set it for the handler
    formatter = Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)

    # Get the root logger
    logger = getLogger()
    logger.addHandler(file_handler)

    return logger


# Get the configured logger
logger = setup_logger()
