import pandas as pd
import openpyxl
import os
import urllib
import datetime
from db_utils.base import Session, Session_ax
import matplotlib.pyplot as plt
import seaborn as sns

with Session() as session:
    # Read table: dimensional_ax.schema_special_plus
    df = pd.read_sql('SELECT * FROM dimensional_ax.schema_special_plus', session.bind)

# df.to_csv('schema_special.csv', index=False)

# ETUVE
# Filter only etuve
df_etuve = df.loc[df['Type'] == 'ETUVE'].copy()




# Puissance moteurs
df_etuve['Tot_puiss_MS'] = df_etuve['MS1'].fillna(0) + df_etuve['MS2'].fillna(0)  + df_etuve['MS3'].fillna(0)  + df_etuve['MS4'].fillna(0)
df_etuve['Tot_puiss_ME'] = df_etuve['ME1'].fillna(0)  + df_etuve['ME2'].fillna(0)  + df_etuve['ME3'].fillna(0)  + df_etuve['ME4'].fillna(0)
df_etuve['Mean_puiss_MS'] = df_etuve['Tot_puiss_MS'] / df_etuve['Nb_MS']
df_etuve['Mean_puiss_ME'] = df_etuve['Tot_puiss_ME'] / df_etuve['Nb_ME']


# DEMARREUR

def moteur2demarrer(power: float) -> str:
    """
    Convert a motor power to a starter code
    """
    map_demarreur = [
        {'min': 0, 'max': 5.5, 'code': None},
        {'min': 7.5, 'max': 9, 'code': 'KV14 535'},
        {'min': 11, 'max': 11, 'code': 'KV14 536'},
        {'min': 15, 'max': 15, 'code': 'KV14 537'},
        {'min': 18.5, 'max': 18.5, 'code': 'KV14 538'},
        {'min': 22, 'max': 22, 'code': 'KV14 539'},
        ]
    for row in map_demarreur:
        if row['min'] <= power <= row['max']:
            return row['code']
    return None

def var2art(power:float, type: str) -> str:
    """
    Convert a variator label to an article code
    """
    if type == 'Direct':
        return None
    map_var = [
         {'min': 0, 'max': 5.5, 'code': None},
        {'min': 7.5, 'max': 9, 'code': 'KV14 535'},
        {'min': 11, 'max': 11, 'code': 'KV14 536'},
        ]
    for row in map_var:
        if row['min'] <= power <= row['max']:
            return row['code']
    return None

def puissance2motor(power: float) -> str:
    map_moteur = [
    {"min": 1.5, "max": 1.5, "code": "KU07 24"},
    {"min": 2.2, "max": 2.2, "code": "KU07 25"},
    {"min": 3.0, "max": 3.0, "code": "KU07 26"},
    {"min": 4.0, "max": 4.0, "code": "KU07 27"},
    {"min": 5.5, "max": 5.5, "code": "KU07 28"},
    {"min": 1.1, "max": 1.1, "code": "KU07 30"},
    # {"min": 0.75, "max": 0.75, "code": "KU07 31"},
    {"min": 0.75, "max": 0.75, "code": "KU07 32"},
    {"min": 7.5, "max": 7.5, "code": "KU08 21"},
    {"min": 9.0, "max": 9.0, "code": "KU08 3"},
    {"min": 9.2, "max": 9.2, "code": "KU08 44"}
]
    if power is None:
        return None
    for row in map_moteur:
        if row['min'] <= power <= row['max']:
            return row['code']

class GetPrice():

    """
    A class to get price from a code, using a cache
    """
    def __init__(self, path='./cache_price.json'):
        import json
        self.path = path
        try:
            with open(path, encoding='utf-8') as f:
                self.cache = json.load(f)
        except FileNotFoundError:
            self.cache = {}

    def update_cache(self):
        import json
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=4)

    def get_price(self, code: str) -> float:
        if code is None:
            return 0
        if code in self.cache:
            return self.cache[code]['price']
        else:
            price, date = self._get_price_from_ax(code)
            self.cache[code] = {'price': price, 'date': date}
            self.update_cache()
            return price

    def _get_price_from_ax(self, code: str) -> (float, datetime.datetime):
        with Session_ax() as session:
            raw_query = """
            SELECT
                TOP 1
                PRICE,
                ACTIVATIONDATE 
            FROM
            AXPROD.dbo.INVENTITEMPRICE IP
            WHERE ITEMID = :code
            AND VERSIONID = ''
            ORDER BY ACTIVATIONDATE DESC
            """
            result = session.execute(raw_query, params={'code': code}).fetchone()
            if result is None:
                return None, None
        price, date = result
        #  Convert data for serialization
        price = float(price)
        date = date.strftime('%Y-%m-%d')
        return price, date

get_price = GetPrice()
get_price.get_price('KU08 21')



for col in ['MS1', 'MS2', 'MS3', 'MS4', 'ME1', 'ME2', 'ME3', 'ME4']:
    # Add a demarrer column for each motor
    demarr_col = col + '_demarr'
    df_etuve[demarr_col] = df_etuve[col].apply(moteur2demarrer)

    # Add a variator column for each motor
    var_col = col + '_var'
    df_etuve[var_col] = df_etuve.apply(lambda x: var2art(x[col], x['Type']), axis=1)

    # Add a motor column for each variator
    motor_col = col + '_motor'
    df_etuve[motor_col] = df_etuve.apply(lambda x: puissance2motor(x[col]), axis=1)

to_price_cols = ['MS1_demarr', 'MS2_demarr', 'MS3_demarr', 'MS4_demarr',
                 'ME1_demarr', 'ME2_demarr', 'ME3_demarr', 'ME4_demarr',
                    'MS1_var', 'MS2_var', 'MS3_var', 'MS4_var',
                    'ME1_var', 'ME2_var', 'ME3_var', 'ME4_var',
                    'MS1_motor', 'MS2_motor', 'MS3_motor', 'MS4_motor',
                    'ME1_motor', 'ME2_motor', 'ME3_motor', 'ME4_motor',
                    ]

# Add a price column for each motor, starter and variator
for col in to_price_cols :
    price_col = col + '_price'
    df_etuve.loc[:, price_col] = df_etuve.loc[:, col].apply(lambda x: GetPrice().get_price(x))

# Add price ofr each AF
df_etuve.loc[:, "code_armoire"] = df_etuve.loc[:, "Num_AF"] + df_etuve.loc[:, "Lettrage"] + 'V1'
df_etuve.loc[:, 'armoire_price'] = df_etuve.loc[:, "code_armoire"].apply(lambda x: GetPrice().get_price(x))

get_price = GetPrice()
get_price.get_price('KU08 21')




