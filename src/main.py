import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def configure_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Meeting Guardian")

    from .scheduler import MeetingGuardianScheduler

    scheduler = MeetingGuardianScheduler()

    if os.getenv("RUN_SUMMARY_ON_START", "false").lower() == "true":
        scheduler.run_daily_summary()

    scheduler.start()


if __name__ == "__main__":
    main()
