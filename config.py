import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    env = os.environ
    admin_etic_user = env["ADMIN_ETIC_USER"]
    admin_etic_password = env["ADMIN_ETIC_PASSWORD"]
    api_rfm_user = env["API_RFM_USER"] # API access to RFM
    api_rfm_password = env["API_RFM_PASSWORD"]
    rfm_temp_user = env["RFM_TEMP_USER"] # temporary access for RFM
    rfm_temp_password = env["RFM_TEMP_PASSWORD"]
    log_path = env["LOG_PATH"]
    ftps_hostname = env["FTPS_HOSTNAME"]
    mqtts_hostname = env["MQTTS_HOSTNAME"]
    root_topic = env["ROOT_TOPIC"]
    rfm_ip = env["RFM_IP"]
    rfm_pk = env["RFM_PK"]
    KEY_NAME = env['ENCR_KEY_NAME']
    sfr_api_key = env["SFR_API_KEY"]
    sfr_instance_france = env["SFR_INSTANCE_FRANCE"]
    sfr_instance_europe = env["SFR_INSTANCE_EUROPE"]
    sfr_api_url = env["SFR_API_URL"]

    crypto_pwd = "".join([chr(158 -ord(c)) for c in env["CRYPTO_PWD"] ])
    # DB_URL = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
    #   user=env['DB_USER'],
    #   password=env['DB_PASSWORD'],
    #   host=env['DB_HOST'],
    #   port=env['DB_PORT'],
    #   name=env['DB_NAME']
    # )

class LocalConfig(Config):
    env = os.environ
    ENV = 'development'
    DEBUG = True
    TESTING = True

    ECHO_SQL = True




class PSGConfigProd(Config):
    env = os.environ
    ENV = 'production'
    DEBUG = False
    TESTING = False

    DB_URL = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
        user=env['LOCALPSG_DB_USER'],
        password=env['LOCALPSG_DB_PASSWORD'],
        host=env['LOCALPSG_DB_HOST'],
        port=env['LOCALPSG_DB_PORT'],
        name=env['LOCALPSG_DB_PROD_NAME'])
    ECHO_SQL = False

class PSGConfigTest(Config):
    env = os.environ
    ENV = 'test'
    DEBUG = False
    TESTING = False

    DB_URL = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
        user=env['LOCALPSG_DB_USER'],
        password=env['LOCALPSG_DB_PASSWORD'],
        host=env['LOCALPSG_DB_HOST'],
        port=env['LOCALPSG_DB_PORT'],
        name=env['LOCALPSG_DB_TEST_NAME'])
    ECHO_SQL = False

class PSGConfigLinode(Config):
    env = os.environ
    ENV = 'test'
    DEBUG = False
    TESTING = False

    DB_URL = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
        user=env['LINODEPSG_DB_USER'],
        password=env['LINODEPSG_DB_PASSWORD'],
        host=env['LINODEPSG_DB_HOST'],
        port=env['LINODEPSG_DB_PORT'],
        name=env['LINODEPSG_DB_NAME'])
    ECHO_SQL = False

class ProdConfig(Config):
    env = os.environ
    ENV = 'test'
    DEBUG = False
    TESTING = False

    DB_URL = 'postgresql://{user}:{password}@{host}:{port}/{name}'.format(
        user=env['OVHPSG_DB_USER'],
        password=env['OVHPSG_DB_PASSWORD'],
        host=env['OVHPSG_DB_HOST'],
        port=env['OVHPSG_DB_PORT'],
        name=env['OVHPSG_DB_NAME'])
    ECHO_SQL = False

SelectedConfig = ProdConfig
# SelectedConfig = PSGConfigTest
