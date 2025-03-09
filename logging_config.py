import logging
from pathlib import Path


def setup_logging(run_dir: Path, run_id):
    log_filename = run_dir / f"{run_id}.log"

    # Create a file handler that logs everything (DEBUG level)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)

    # Create a stream handler that logs only INFO and above
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)

    # Define a common format for both handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Get the root logger and set its level to DEBUG
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Add both handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
