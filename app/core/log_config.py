import logging
import sys


def setup_logging(service_name: str):
    logging.basicConfig(
        level=logging.INFO,
        format=f"%(asctime)s | {service_name} | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )
    logging.getLogger("pika").setLevel(logging.WARNING)
    return logging.getLogger(service_name)
