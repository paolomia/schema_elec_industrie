import os
import sys
import logging
import textwrap
from db_utils.base import Session
from config import SelectedConfig as script_conf
from db_utils.tables import LogAutoconfigM
import datetime
import pathlib

os_username = os.getlogin()

# Create log file if it does not exist
relative_log_path = script_conf.log_path
current_dir = pathlib.Path(__file__).parent.resolve()
abs_log_path = current_dir.joinpath(relative_log_path)
dir_log = os.path.dirname(abs_log_path)
if not os.path.exists(dir_log):
    os.makedirs(dir_log)
if not os.path.exists(abs_log_path):
    with open(abs_log_path, 'a'):
        pass

class DBHandler(logging.Handler):
    """
    https://gist.github.com/guoqiao/dbf5d7c016d5cb4816392497fc14f862
    Logging Handler for DB
    """
    def emit(self, record):
        loc_asctime = datetime.datetime.strptime(record.asctime, "%Y-%m-%d %H:%M:%S")
        utc_ascitime = loc_asctime.astimezone(datetime.timezone.utc)
        obj = LogAutoconfigM(
                logger=record.name,
                level=record.levelname,
                msg=record.msg,
                datetime=utc_ascitime,
                user=os_username,
            )
        with Session() as session:
            session.add(obj)
            session.commit()


class MultiLineFormatter(logging.Formatter):
    def format(self, record):
        message = record.msg
        record.msg = ''
        header = super().format(record)
        msg = textwrap.indent(message, ' ' * len(header)).lstrip()
        record.msg = message
        return header + msg


level    = logging.DEBUG
format   = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
formatter = MultiLineFormatter(
    fmt=f'%(asctime)s %(name)-15s {os_username:<16} %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
handlers = [logging.FileHandler(abs_log_path, encoding='utf-8'), logging.StreamHandler(sys.stdout), DBHandler()]

# logging.basicConfig(level=level, format=format, handlers=handlers)


def make_logger(name):
    logger = logging.getLogger(name)
    for handler in handlers:
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# ! Faire très attention à mélanger query et logging ! Si on log le contenu d'une query en dehors
# du context manager, il semble que la session soit reouverte, et en cumulant avec le logging,
# la session ne vient pas refermée dans la suite
# Ce qui peut mener à un QueuePool limit error
# Faire toruner la commande:
# select * from pg_stat_activity;
# dans la console du ddb peut aider à voir les connexions ouvertes et diagnostiquer le problème


