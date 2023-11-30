import pandas as pd
from src.db_utils.ax_helper import get_equip_info, add_from_equip
from src.db_utils.tables import(
    EquipM,
    SiteM,
    FirmwareAlarmM,
    RasConfigM,
    Ras2EquipM,
    ConfigBaseM,
    FirmwareIpleM,
    RasM,
    RawFileM)
from src.db_utils.base import Session, engine
import io
from cryptography.fernet import Fernet
import hashlib
from  typing import  Optional
import pandas as pd
# Init the logger
from src.log_init import make_logger
logger = make_logger('db_helper')


def test_postgres(suppress_error=False):
    """Test connexion to postgres database"""
    from src.db_utils.base import Session_ax
    try:
        with engine.connect() as cnx:
            cnx.execute('select id from client limit 1')
    except:
        if suppress_error:
            print("Impossible se connecter à la BDD")
            return False
        raise RuntimeError("Le serveur Postgresql n'est pas joignable")
    return True
# Test the server
# test_postgres()

# SOME SQL REQUESTS READY TO USE


def already_configurated(ras_code: str) -> bool:
    with Session() as session:
        results = session.query(RasM, RasConfigM).join(RasConfigM).filter(RasConfigM.code_ras==ras_code, RasM.code_config == RasConfigM.code_config).all()
    return len(results) > 0


def upsert_instance(instance_model_orig, key=None, keys=None, do_not_compare=[], do_not_modify=[]) -> str:
    """
    Given a `instance_model`, it checks if it is already recorded using `key` (or `keys`). If not, it is appended
    and committed, otherwise it checks if any value, not in `do_not_compare` list, is different between
    recorded and `instance_model`.
    If there is any difference, it updates ALL VALUES excepted `do_not_modify` values.  `do_not_compare` values are
    modified too, if they are not included in `do_not`modify` values.
    The id column is not affected.

    You can use a single string in `key`, or a list of string in `keys`

    It returns:
    - 'added' : the instance was not found and it has benn added
    - 'updated': the instance was found, but it has been modified
    - 'nothing': the instance was found and all attributes were the same (no actions performed)

    Ex:  upsert_data(ax_config, "code_ras", ["processed"])
    """
    from copy import deepcopy
    # deal with a single key
    if keys is None:
        if key is None:
            raise RuntimeError("You need to specify at least one key")
        else:
            keys = [key]

    from copy import deepcopy

    # Create a copy for avoiding DetachedInstanceError
    instance_model = deepcopy(instance_model_orig)
    model = instance_model.__class__
    with Session() as session:
        # Check if the instance already exists
        from sqlalchemy.orm.exc import DetachedInstanceError
        try:
            filters = [getattr(model, key) == getattr(instance_model, key) for key in keys]
            query = session.query(model).filter(*filters)
            exists = query.scalar()
        except DetachedInstanceError:
            raise DetachedInstanceError("On ne peut pas accéder une instance suite à un commit")
        if exists:
            # Check if the recorder values has some difference with instance_model
            out = "nothing"
            always_ignore = ["_sa_instance_state", "id"]
            do_not_compare += always_ignore  # add sa_instance to the list of attribute to ignore in comparing
            do_not_modify += always_ignore
            found = query[0]
            for key, new_value in instance_model.__dict__.items():
                if key not in do_not_compare:
                    # compare among all attributes not in do_not_compare list
                    if new_value != getattr(found, key):
                        out = "updated"
                        # break
            if out == "updated":
                # modify all attributes not in do_not_modify list
                for key, new_value in instance_model.__dict__.items():
                    if key not in do_not_modify:
                        setattr(found, key, new_value)
        else:
            # Append the instance if it does not exist
            out = "added"
            session.add(instance_model)
            try:
                session.commit()
            except Exception as e:
                logger.error(str(e))
                raise e
        if out != "nothing":
            try:
                session.commit()
            except Exception as e:
                logger.error(str(e))
                raise e
    return out

def get_raw_file(file_name:str) -> io.BytesIO:
    """Get raw file from the DB"""
    with Session() as session:
        raw_file = session.query(RawFileM).\
            filter(RawFileM.file_name == file_name).one()
    binary_data = io.BytesIO(raw_file.binary_data)
    return binary_data
#
# def upsert_instance_keys(instance_model_orig, keys: list, do_not_compare=[], do_not_modify=[]) -> str:
#     """
#     Given a `instance_model`, it checks if it is already recorded using `key`. If not, it is appended
#     and committed, otherwise it checks if any value, not in `do_not_compare` list, is different between
#     recorded and `instance_model`.
#     If there is any difference, it updates ALL VALUES excepted `do_not_modify` values.  `do_not_compare` values are
#     modified too, if they are not included in `do_not`modify` values.
#     The id column is not affected.
#
#     It returns:
#     - 'added' : the instance was not found and it has benn added
#     - 'updated': the instance was found, but it has been modified
#     - 'nothing': the instance was found and all attributes were the same (no actions performed)
#
#     Ex:  upsert_data(ax_config, "code_ras", ["processed"])
#     """
#     from copy import deepcopy
#
#     # Create a copy for avoiding DetachedInstanceError
#     instance_model = deepcopy(instance_model_orig)
#     model = instance_model.__class__
#     with Session() as session:
#         # Check if the instance already exists*
#         from sqlalchemy.orm.exc import DetachedInstanceError
#         try:
#             filters = [getattr(model, key) == getattr(instance_model, key) for key in keys]
#             query = session.query(model).filter(*filters)
#             exists = query.scalar()
#         except DetachedInstanceError:
#             raise DetachedInstanceError("On ne peut pas accéder une instance suite à un commit")
#     if exists:
#         # Check if the recorder values has some difference with instance_model
#         out = "nothing"
#         always_ignore = ["_sa_instance_state", "id"]
#         do_not_compare += always_ignore  # add sa_instance to the list of attribute to ignore in comparing
#         do_not_modify += always_ignore
#         found = query[0]
#         for key, new_value in instance_model.__dict__.items():
#             if key not in do_not_compare:
#                 # compare among all attributes not in do_not_compare list
#                 if new_value != getattr(found, key):
#                     out = "updated"
#                     # break
#         if out == "updated":
#         # modify all attributes not in do_not_modify list
#             for key, new_value in instance_model.__dict__.items():
#                 if key not in do_not_modify:
#                     setattr(found, key, new_value)
#     else:
#         # Append the instance if it does not exist
#         out = "added"
#         session.add(instance_model)
#         try:
#             session.commit()
#         except Exception as e:
#             logger.error(str(e))
#             raise e
#     if out != "nothing":
#         try:
#             session.commit()
#         except Exception as e:
#             logger.error(str(e))
#             raise e
#     return out

if __name__ == "__main__":
    ras_code = "AF003989-A-AV1"
    print(already_configurated(ras_code))