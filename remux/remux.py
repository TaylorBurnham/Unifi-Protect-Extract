#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from datetime import datetime
from dateutil import parser as dateparse
from utilities.config import Config
from utilities.processing import UBVRemux
from utilities.cloudkey import CloudKey


def str2bool(v):
    # Sourced from https://stackoverflow.com/a/43357954/931279
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_date(d):
    try:
        date = dateparse.parse(d)
    except dateparse.ParserError as e:
        logger.warning(
            f"Bad date passed: {d}")
        logger.critical(
            f"{str(e)}"
        )
        sys.exit(1)
    return date.date()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Unifi Protect Extract - A Working Title!"
    )
    parser.add_argument(
        "--environment", "-e",
        help="The location of the .env file. Defaults to '.env'",
        default=None
    )
    parser.add_argument(
        "--parse-date", "-pd",
        help="Parse UBV files from a specific date."
    )
    parser.add_argument(
        "--parse-all", "-pa",
        type=str2bool, nargs='?', const=True, default=False,
        help="Parse all UBV files available."
    )
    parser.add_argument(
        "--list-dates", "-ls",
        type=str2bool, nargs='?', const=True, default=False,
        help="List all of the dates available for parsing."
    )
    # parser.add_argument(
    #     "--no-cleanup", "-nc",
    #     type=str2bool, nargs='?', const=True, default=False,
    #     help="Do not remove UBV files after processing."
    # )
    return parser


if __name__ == "__main__":
    # Parse Arguments
    p = parse_arguments()
    args = p.parse_args()
    print(args)
    # Handle the default environment config
    if args.environment:
        if os.path.exists(args.environment):
            config = Config(dotenv=args.environment)
        else:
            raise FileNotFoundError(
                f"Cannot locate .env file at {args.environment}"
            )
            sys.exit(1)
    else:
        config = Config(dotenv='.env')
    # Create the logging object
    logger = logging.getLogger()
    logging_handlers = []
    # Add the stdout
    logging_handlers.append(logging.StreamHandler(sys.stdout))
    if config.logs.format:
        log_format = config.logs.format
    else:
        log_format = '[%(asctime)s] {%(filename)s:%(lineno)d} ' \
            '%(levelname)s - %(message)s'
    if config.logs.level:
        log_level = config.logs.level
    else:
        log_level = logging.INFO
    # Add the log file if exists
    if config.logs.logfile:
        os.makedirs(config.logs.logpath, exist_ok=True)
        logdate = datetime.now().strftime("%F")
        logfile = os.path.join(
            config.logs.logpath, f"Unifi-Protect-Extract-{logdate}.log"
        )
        logging_handlers.append(
            logging.FileHandler(
                logfile, mode="a"
            )
        )
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=logging_handlers
    )
    logger.info("Initialized.")
    cloudkey = CloudKey(config=config.cloudkey)

    # TODO - Implement cleanup
    # Determine if we are being destructive, invert the param
    # DESTRUCTIVE = not args.no_cleanup
    # if DESTRUCTIVE:
    #     logger.warning(
    #         "Destructive is set to True. UBV files will be removed "
    #         "after being parsed.")
    # else:
    #     logger.info(
    #         "Destructive is set to False. UBV files will be retained.")

    # Handle the arguments
    if args.list_dates:
        logger.info("Listing all Dates with UBV Files...")
        cameras = cloudkey.get_cameras()
        remux = UBVRemux(config=config.paths, auto_create_tmp=False)
        remux.get_ubv_filecounts(cameras)
    elif args.parse_date:
        date = parse_date(args.parse_date)
        logger.info(f"Parsing all UBV Files on {date}")
        cameras = cloudkey.get_cameras()
        remux = UBVRemux(config=config.paths)
        remux.remux_ubv_by_date(
            date, cameras
        )
        logger.info(f"Completed Parsing {date}. Cleaning up...")
        os.rmdir(remux.temp)
        sys.exit(0)
    elif args.parse_all:
        logger.info(
            f"Parsing all UBV files available in {config.paths.files}")
        cameras = cloudkey.get_cameras()
        remux = UBVRemux(config=config.paths)
        ubv_files = remux.get_ubv_files()
        for date in sorted(ubv_files.keys()):
            remux.remux_ubv_by_date(
                date, cameras
            )
        logger.info("Completed Parsing all files. Cleaning up...")
        os.rmdir(remux.temp)
        sys.exit(0)
    else:
        logger.warning("No arguments passed.")
        sys.exit(1)
