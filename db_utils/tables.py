from sqlalchemy import (
    Table,
    Column,
    Integer,
    String,
    LargeBinary,
    MetaData,
    ForeignKey,
    Float,
    Date,
    ForeignKey,
    Enum,
    DateTime,
    Boolean,
    UniqueConstraint)
from sqlalchemy.orm import relationship, backref
from src.db_utils.base import Base, engine, ReprTable
import datetime

class MQTTUserM(Base, ReprTable):
    __tablename__ = 'mqtt_user'

    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('user.username'), nullable=False, index=True)
    hostname = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False)
    mqtt2ras = relationship("RasConfigM", backref="mqtt_user")


class FTPUserM(Base, ReprTable):
    __tablename__ = 'ftp_user'

    id = Column(Integer, primary_key=True)
    username = Column(String, ForeignKey('user.username'), nullable=False, index=True)
    hostname = Column(String, nullable=False, index=True)
    csv_dir = Column(String, nullable=False) # Directory in the FTP Server
    root_dir = Column(String)
    over_tls = Column(Boolean, nullable=False)
    ftp2ras = relationship("RasConfigM", backref="ftp_user_ref")


class UserM(Base, ReprTable):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True, index=True) # docker style code
    encrypted_pwd_FTP = Column(LargeBinary, nullable=False)
    encrypted_pwd_MQTT = Column(LargeBinary, nullable=False)
    encrypted_pwd_3 = Column(LargeBinary, nullable=False)
    encrypted_pwd_4 = Column(LargeBinary, nullable=False)
    encrypted_pwd_5 = Column(LargeBinary, nullable=False)
    user2ftp = relationship("FTPUserM", backref="user")
    user2mqtt = relationship("MQTTUserM", backref="user1")
    user2ras = relationship("Ras2UserM", backref="user2")

    def __repr__(self):
        return self._repr(username=self.username)


class RasConfigM(Base, ReprTable):
    __tablename__ = 'ras_config'

    id = Column(Integer, primary_key=True)
    code_config = Column(String, nullable=False, unique=True, index=True) #code ras + timestamp
    code_ras = Column(String, ForeignKey('projet_config.code_ras'))
    encrypted_config = Column(LargeBinary)
    ftp_id = Column(Integer, ForeignKey('ftp_user.id'))
    mqtt_id = Column(Integer, ForeignKey('mqtt_user.id'))
    config_base = Column(String, ForeignKey('config_base.version_config'), nullable=False)
    date_creation = Column(DateTime, nullable=False)
    date_modification = Column(DateTime, nullable=False) # En réalité la configuration n'est pas vraiment modifiée. La seule chose modifiée est ce champ
    checksum = Column(String, unique=True, index=True)
    commentaire = Column(String)

    rasconfig2ras = relationship("RasM", backref="ras_config_ref")

    def __repr__(self):
        return self._repr(code_config=self.code_config,
                          date_modification=self.date_modification,
                          config_base=self.config_base)



class RasM(Base, ReprTable):
    __tablename__ = 'ras'

    id = Column(Integer, primary_key=True)
    # code_ras = Column(String, nullable=False, unique=True) #code ras is associated only to configs
    code_config = Column(String, ForeignKey('ras_config.code_config'))
    imei = Column(String)
    encrypted_pk = Column(LargeBinary)
    nom = Column(String)
    # uppercase hex md5 hash of product key
    hash_pk = Column(String, unique=True)
    # première configuration du RAS
    date_first_config = Column(DateTime, nullable=True)
    # dernière configuration du Ras
    date_last_config = Column(DateTime, nullable=True)
    # Il faut ajouter le ras au rfm
    rfm_to_do = Column(Boolean, default=False)
    # L'utilisateur temporaire pour la syncronization avec le RFm a été ajouté
    rfm_temp_user = Column(Boolean, default=False)
    # Le ras a été ajouté à la liste des sites sur le RFM
    rfm_added_site_list = Column(Boolean, default=False)
    # Id du site sur le RFM associé au ras
    rfm_site_id = Column(Integer)
    # Le rfm et le RAS sont synchronisé
    rfm_synchronized = Column(Boolean, default=False)

    def __repr__(self):
        return self._repr(imei=self.imei,
                          nom=self.nom)

class RasReattribueM(Base, ReprTable):
    __tablename__ = 'ras_reattribue'

    id = Column(Integer, primary_key=True)
    # code_ras = Column(String, nullable=False, unique=True) #code ras is associated only to configs
    old_code_config = Column(String, ForeignKey('ras_config.code_config'))
    nom = Column(String)
    # uppercase hex md5 hash of product key
    hash_pk = Column(String, unique=True)
    # première configuration du RAS
    date_creation = Column(DateTime, nullable=True)

    def __repr__(self):
        return self._repr(nom=self.nom)



class FirmwareIpleM(Base, ReprTable):
    __tablename__ = 'firmware_iple'

    id = Column(Integer, primary_key=True)
    version = Column(String, unique=True)
    path = Column(String) # Where the firmware setup file is located
    description = Column(String)
    file_name = Column(String, ForeignKey('raw_file.file_name'), nullable=True)

    firm_iple2conf = relationship("ConfigBaseM", backref="firmware_iple_ref")


class FirmwareAlarmM(Base, ReprTable):
    __tablename__ = 'firmware_alarm'

    id = Column(Integer, primary_key=True)
    version = Column(String, unique=True)
    path = Column(String) # Where the firmware setup file is located
    description = Column(String)
    file_name = Column(String, ForeignKey('raw_file.file_name'), nullable=True)

    firm_ca2conf = relationship("ConfigBaseM", backref="firmware_ca_ref")


class ModeleRouteurM(Base, ReprTable):
    __tablename__ = 'modele_routeur'

    id = Column(Integer, primary_key=True)
    nom = Column(String, unique=True)
    description = Column(String)
    gsm = Column(Boolean)
    ethernet = Column(Boolean)

    modele2conf = relationship("ConfigBaseM", backref="modele_ref")


class ConfigBaseM(Base, ReprTable):
    __tablename__ = 'config_base'

    id = Column(Integer, primary_key=True)
    version_config = Column(String, unique=True, index=True)
    date = Column(Date)
    config = Column(String)
    yaml = Column(String)
    type_config = Column(String, ForeignKey('type_config.type_config'))
    schema_config = Column(String, ForeignKey('schema_config.schema_config'))
    config_base = Column(String)
    description = Column(String)
    version_iple = Column(String, ForeignKey('firmware_iple.version'))
    version_alarm = Column(String, ForeignKey('firmware_alarm.version'))
    version_automate = Column(String)
    modele_routeur = Column(String, ForeignKey('modele_routeur.nom'))

    versiondefault2config = relationship("VersionDefaultM", backref="config_base_ref")
    rasconfig2baseconfig = relationship("RasConfigM", backref="config_base_ref")
    projet2config = relationship("ProjetConfigM", backref="config_base_ref")

    def __repr__(self):
        return self._repr(version_config=self.version_config,
                          version_automate=self.version_automate,
                          version_iple=self.version_iple,
                          version_alarm=self.version_alarm)



class TypeConfigM(Base, ReprTable):
    __tablename__ = 'type_config'

    id = Column(Integer, primary_key=True)
    type_config = Column(String, unique=True)
    commentaire = Column(String)

    schema2type = relationship("SchemaConfigM", backref="type_config_ref")
    schemadefault2type = relationship("SchemaDefaultM", backref="type_config_ref")
    configbase2type = relationship("ConfigBaseM", backref="type_config_ref")
    projet2type = relationship("ProjetConfigM", backref="type_config_ref")

class SchemaConfigM(Base, ReprTable):
    __tablename__ = 'schema_config'

    id = Column(Integer, primary_key=True)
    type_config = Column(String, ForeignKey('type_config.type_config'), nullable=False)
    schema_config = Column(String, unique=True)
    commentaire = Column(String)
    schemadefault2schema = relationship("SchemaDefaultM", backref="schema_config_ref")
    versiondefault2schema = relationship("VersionDefaultM", backref="schema_config_ref")
    configbase2schema = relationship("ConfigBaseM", backref="schema_config_ref")
    projet2schema = relationship("ProjetConfigM", backref="schema_config_ref")


class SchemaDefaultM(Base, ReprTable):
    __tablename__ = 'schema_default'

    id = Column(Integer, primary_key=True)
    type_config = Column(String, ForeignKey('type_config.type_config'), unique=True)
    schema_config = Column(String, ForeignKey('schema_config.schema_config'))

class VersionDefaultM(Base, ReprTable):
    __tablename__ = 'version_default'

    id = Column(Integer, primary_key=True)
    schema_config = Column(String, ForeignKey('schema_config.schema_config'), unique=True)
    version_config = Column(String, ForeignKey('config_base.version_config'))

class Sim2ImeiM(Base, ReprTable):
    __tablename__ = 'sim2imei'

    id = Column(Integer, primary_key=True)
    msisdn = Column(String, unique=True)
    imei = Column(String)
    sim_name = Column(String)
    code_ras = Column(String)
    instance = Column(String)
    code_instance = Column(String)
    forfait = Column(String)
    creation_date = Column(DateTime)
    first_activation_date = Column(DateTime)
    lat = Column(Float)
    long = Column(Float)

class SimCommunicationM(Base, ReprTable):
    __tablename__ = 'sim_communication'

    id = Column(Integer, primary_key=True)
    msisdn = Column(String)
    last_communication_status = Column(String)
    timestamp = Column(DateTime)
    last_communication = Column(DateTime)

class ProjetConfigM(Base, ReprTable):
    __tablename__ = 'projet_config'

    id = Column(Integer, primary_key=True)
    code_ras = Column(String, nullable=False, unique=True, index=True)
    type_config = Column(String, ForeignKey('type_config.type_config'))
    schema_config = Column(String, ForeignKey('schema_config.schema_config'))
    version_config = Column(String, ForeignKey('config_base.version_config'))
    commentaire = Column(String)
    infrastructure = Column(String)
    nom = Column(String)
    date_creation = Column(DateTime, nullable=True)
    date_modification = Column(DateTime, nullable=True)
    date_debit = Column(DateTime, nullable=True)
    migrated = Column(Boolean, nullable=False)
    created_by = Column(String, nullable=True)


    projet2config = relationship("RasConfigM", backref="projet_config_ref")
    projet2rasequip = relationship("Ras2EquipM", backref="projet_config_ref")

    def __repr__(self):
        return self._repr(code_ras=self.code_ras,
                          type_config=self.type_config
                          )


class Ras2EquipM(Base, ReprTable):
    __tablename__ = 'ras2equip'

    id = Column(Integer, primary_key=True)
    code_ras = Column(String, ForeignKey('projet_config.code_ras'), nullable=False, index=True)
    code_equip = Column(String, ForeignKey('equip.code_equip'), nullable=False, index=True)
    ordre_equip = Column(Integer, nullable=False)
    description = Column(String)

    def __repr__(self):
        return self._repr(code_ras=self.code_ras,
                          code_equip=self.code_equip)


class Ras2UserM(Base, ReprTable):
    __tablename__ = 'ras2user'

    id = Column(Integer, primary_key=True)
    code_ras = Column(String, ForeignKey('projet_config.code_ras'), nullable=False, index=True)
    username = Column(String, ForeignKey('user.username'), nullable=False, index=True)

    def __repr__(self):
        return self._repr(code_ras=self.code_ras,
                          username=self.username)


class ClientM(Base, ReprTable):
    __tablename__ = 'client'

    id = Column(Integer, primary_key=True)
    code_client = Column(String, nullable=False, unique=True, index=True)
    raison_sociale = Column(String, nullable=False)
    adresse = Column(String)
    ville = Column(String)
    code_postal = Column(String)
    pays = Column(String)
    siren = Column(String)
    clientsite = relationship("SiteM", backref="client")

    def __repr__(self):
        return self._repr(code_client=self.code_client,
                          raison_sociale=self.raison_sociale)


class SiteM(Base, ReprTable):
    __tablename__ = 'site'

    id = Column(Integer, primary_key=True)
    code_client = Column(String, ForeignKey('client.code_client'), nullable = False, index=True)
    code_site = Column(String, nullable=False, unique=True, index=True)
    adresse = Column(String, nullable=False)
    ville = Column(String, nullable=False)
    pays = Column(String, nullable=False)
    code_postal =  Column(String, nullable=False)
    long = Column(Float)
    lat =  Column(Float)
    nom = Column(String)
    site2equip = relationship("EquipM", backref="site")
    site2contact = relationship("ContactM", backref="site1")

    def __repr__(self):
        return self._repr(code_client=self.code_client,
                          code_site=self.code_site,
                          ville=self.ville)


class EquipM(Base, ReprTable):
    __tablename__ = 'equip'

    id = Column(Integer, primary_key=True)
    code_site = Column(String, ForeignKey('site.code_site'), nullable=False)
    code_equip = Column(String, nullable=False, unique=True) # AF123456-A
    type = Column(String, nullable=False) # cabine
    descr = Column(String, nullable=True) # Luxia 700S
    equip2rasequip = relationship("Ras2EquipM", backref="equip0")
    equip2speccabine = relationship("SpecCabineM", backref="equip1")
    equip2datecabine = relationship("DateCabineM", backref="equip2")

    def __repr__(self):
        return self._repr(code_equip=self.code_equip,
                          type=self.type,
                          descr=self.descr)

class ContactM(Base, ReprTable):
    __tablename__ = 'contact'

    id = Column(Integer, primary_key=True)
    code_site = Column(String, ForeignKey('site.code_site'), nullable=False, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    email = Column(String, nullable=True)
    type = Column(String)
    telephone = Column(String)
    telephone2 = Column(String)



    def __repr__(self):
        return self._repr(code_equip=self.code_equip,
                          descr=self.descr)


class SpecCabineM(Base, ReprTable):
    __tablename__ = 'spec_cabine'

    id = Column(Integer, primary_key=True)
    code_equip = Column(String,  ForeignKey('equip.code_equip'), nullable=False, index=True)
    model = Column(String, nullable=False)
    position_machine = Column(String, nullable=False)
    armoire = Column(String, nullable=True)

    def __repr__(self):
        return self._repr(code_equip=self.code_equip,
                          model=self.model)


class DateCabineM(Base, ReprTable):
    __tablename__ = 'date_cabine'

    id = Column(Integer, primary_key=True)
    code_equip = Column(String,  ForeignKey('equip.code_equip'), nullable=False, index=True)
    date_mise_service = Column(Date)
    date_expedition = Column(Date)

    def __repr__(self):
        return self._repr(code_equip=self.code_equip,
                          date_mise_service=self.date_mise_service)


class RawFileM(Base, ReprTable):
    """A table containing raw file"""
    __tablename__ = 'raw_file'

    id = Column(Integer, primary_key=True)
    file_name = Column(String, nullable=False, unique=True)
    file_size = Column(Integer)
    md5sum = Column(String)
    description = Column(String, nullable=True)
    binary_data = Column(LargeBinary, nullable=True)

    raw2iple = relationship("FirmwareIpleM", backref="rawfile_iple_ref")
    raw2alarm = relationship("FirmwareAlarmM", backref="rawfile_alarm_ref")

    def __repr__(self):
        return self._repr(file_name=self.file_name,
                          file_size=self.file_size)




class LogAutoconfigM(Base, ReprTable):
    """Log messages"""
    __tablename__ = 'log_autoconfig'

    id = Column(Integer, primary_key=True)
    datetime = Column(DateTime, nullable=False)
    logger = Column(String)
    user = Column(String)
    level = Column(String)
    msg = Column(String)

    def __repr__(self):
        return self._repr(datetime=self.datetime,
                          module=self.module,
                          user=self.user,
                          level=self.level,
                          msg=self.msg,)


class LogPipelineM(Base, ReprTable):
    """Log messages"""
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    type = Column(String)
    level = Column(String)
    message = Column(String)

    def __repr__(self):
        return self._repr(timestamp=self.timestamp,
                          type=self.type,
                          level=self.level,
                          message=self.message,)


class MailLogM(Base, ReprTable):
    """Log messages"""
    __tablename__ = 'mail_log'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    object = Column(String)
    corps = Column(String)
    destinataires = Column(String)
    resume = Column(String)
    jours_avant_relance = Column(Integer)

import sqlalchemy.types as types

def lower(s):
    """converts to lowercase if a string. Otherwise return None"""
    if isinstance(s, str):
        return s.lower()

class LowerCaseText(types.TypeDecorator):
    '''Converts strings to lower case on the way in.'''
    # https://stackoverflow.com/questions/14048562/what-is-the-correct-way-to-make-sqlalchemy-store-strings-as-lowercase
    impl = types.Text

    def process_bind_param(self, value, dialect):
        return lower(value)


class AXConfigurationM(Base, ReprTable):

    """Tableau avec les configurations des routeurs à partir de la nomenclature des armoires"""
    __tablename__ = 'ax_config'

    id = Column(Integer, primary_key=True)
    equip = Column(String, nullable=False)
    code_ras = Column(String, unique=True, nullable=False)
    equip1 = Column(String, nullable=True)
    equip2 = Column(String, nullable=True)
    equip3 = Column(String, nullable=True)
    equip4 = Column(String, nullable=True)
    equip5 = Column(String, nullable=True)
    date_debit = Column(DateTime, nullable=True)
    created_by = Column(String, nullable=True)
    compte_client = Column(String)

    type_config = Column(String)
    schema_config = Column(String)
    version_config = Column(String)

    processed = Column(Boolean)

    def get_equipments(self):
        """Return the list of connected equipments"""
        equips = [self.equip1, self.equip2, self.equip3, self.equip4, self.equip5]
        return [equip for equip in equips if equip is not None]

    def get_equip_dict(self):
        """Return the dict of connected equipments"""
        equips = [self.equip1, self.equip2, self.equip3, self.equip4, self.equip5]
        return {i: equip for i, equip in zip(range(1, len(equips)), equips) if equip is not None}

    @property
    def type_config_lower(self):
        type_config = self.type_config
        # Replace "no_data" by "nodata" for preventing errors
        if type_config.lower() == 'no_data':
            type_config = 'nodata'
        return lower(type_config)

    @property
    def version_config_lower(self):
        return lower(self.version_config)

    @property
    def schema_config_lower(self):
        return lower(self.schema_config)


    def __repr__(self):
        return self._repr(code_ras=self.code_ras,
                          type_config=self.type_config,
                          equip1=self.equip1,
                          processed=self.processed)
    # MAke a new model from:

    # -- dimensional_ax.spec_equip
    # definition
    #
    # -- Drop
    # table
    #
    # -- DROP
    # TABLE
    # dimensional_ax.spec_equip;
    #
    # CREATE
    # TABLE
    # dimensional_ax.spec_equip(id
    # serial4
    # NOT
    # NULL, code_equip
    # varchar
    # NOT
    # NULL, nom_spec
    # varchar
    # NULL, value
    # varchar
    # NULL, date_creation
    # timestamp
    # NULL
    # DEFAULT
    # CURRENT_TIMESTAMP, CONSTRAINT
    # spec_cabine_pkey
    # PRIMARY
    # KEY(id)
    # );
    # CREATE
    # INDEX
    # ix_spec_cabine_code_equip
    # ON
    # dimensional_ax.spec_equip
    # USING
    # btree(code_equip);

class SpecEquipM(Base, ReprTable):
    """Tableau avec les specs techniques des équipements"""
    __tablename__ = 'spec_equip'
    __table_args__ = {'schema': 'dimensional_ax'}

    id = Column(Integer, primary_key=True)
    code_equip = Column(String, nullable=False)
    nom_spec = Column(String, nullable=False)
    value = Column(String, nullable=True)
    date_creation = Column(DateTime, nullable=True, default=datetime.datetime.now)
    date_modification = Column(DateTime, nullable=True, default=datetime.datetime.now)

    def __repr__(self):
        return self._repr(code_equip=self.code_equip,
                          nom_spec=self.nom_spec,
                          value=self.value,
                          date_creation=self.date_creation)


if __name__ == "__main__":
    # Base.metadata.create'all will find all subclasses of BaseModel, and create these tables in the database, which is equivalent to 'create table'
    # Uncomment to create all tables
    Base.metadata.create_all(engine)