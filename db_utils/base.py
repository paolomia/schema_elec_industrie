# https://auth0.com/blog/sqlalchemy-orm-tutorial-for-python-developers/
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlalchemy as sa
import urllib
from config import SelectedConfig as conf
import typing


ca_path = "src/db_utils/ca_postgresql.crt"
ssl_args = {
    'sslrootcert': ca_path,
    'sslmode': 'require'
    }
engine = create_engine(conf.DB_URL, echo=conf.ECHO_SQL, connect_args=ssl_args)
# engine_test = create_engine(conf.DB_URL, echo=conf.ECHO_SQL,  connect_args={'connect_timeout': 4})
Base = declarative_base()
Session = sessionmaker(bind=engine)

params = urllib.parse.quote_plus("Driver={ODBC Driver 11 for SQL Server};"
                                 "Server=192.1.1.18;"
                                 "Database=Entrepot_Production_V2;"
                                 "uid=sa;"
                                 "pwd=neomia")
connection_url = "mssql+pyodbc:///?odbc_connect={}".format(params)
engine_ax = create_engine(connection_url, echo=conf.ECHO_SQL)
BaseAx = declarative_base()
Session_ax = sessionmaker(bind=engine_ax)


class ReprTable:
    """A class for fast implementing the __repr__ method in tables"""

    def __repr__(self) -> str:
        return self._repr(id=self.id)

    def _repr(self, **fields: typing.Dict[str, typing.Any]) -> str:
        field_strings = []
        at_least_one_attached_attribute = False
        for key, field in fields.items():
            try:
                field_strings.append(f'{key}={field!r}')
            except sa.orm.exc.DetachedInstanceError:
                field_strings.append(f'{key}=DetachedInstanceError')
            else:
                at_least_one_attached_attribute = True
        if at_least_one_attached_attribute:
            return f"<{self.__class__.__name__}({','.join(field_strings)})>"
        return f"<{self.__class__.__name__} {id(self)}>"

