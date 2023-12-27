import pandas as pd
import openpyxl
import os
import urllib
import datetime
from db_utils.base import Session, Session_ax
import matplotlib.pyplot as plt
import seaborn as sns

# DEMARREUR

def moteur2demarrer(power: float) -> str:
    """
    Convert a motor power to a starter code
    """
    map_demarreur = [
        {'min': 0, 'max': 5.5, 'code': None},
        {'min': 7.5, 'max': 9.2, 'code': 'KV14 535'},
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
    if type.lower() == 'direct':
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

map_moteur = [
    # {"min": 0.75, "max": 0.75, "code": "KU07 31"},
    #     Je ne trouve pas de standard < 0.75 donc je prends le plus proche
    {"min": 0, "max": 0.75, 'power': 0.75, "code": "KU07 32"},
    {"min": 1.1, "max": 1.1, 'power': 1.1, "code": "KU07 30"},
    {"min": 1.5, "max": 1.5, 'power': 1.5, "code": "KU07 24"},
    {"min": 2.2, "max": 2.2, 'power': 2.2, "code": "KU07 25"},
    {"min": 3.0, "max": 3.0, 'power': 3.0, "code": "KU07 26"},
    {"min": 4.0, "max": 4.0, 'power': 4.0, "code": "KU07 27"},
    {"min": 5.5, "max": 5.5, 'power': 5.5, "code": "KU07 28"},
    {"min": 7.5, "max": 7.5, 'power': 7.5, "code": "KU08 21"},
    {"min": 9.0, "max": 9.0, 'power': 9, "code": "KU08 3"},
    {"min": 9.2, "max": 9.2, 'power': 9.2, "code": "KU08 44"},
    {"min": 11, "max": 11, 'power': 11, "code": "KU08 25"},
    {"min": 15, "max": 15, 'power': 15, "code": "KU08 26"},
    {"min": 18.5, "max": 18.5, 'power': 18.5, "code": "KU08 27"},
    {"min": 22, "max": 22, 'power': 22, "code": "KU08 28"},

]
def puissance2motor(power: float) -> str:

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
            --AND VERSIONID = ''
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

class GetADV():

    """
    A class to get price from a code, using a cache
    """
    def __init__(self, path='./cache_adv.json'):
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

    def get_adv(self, code: str) -> float:
        if code is None:
            return 0
        if code in self.cache:
            return self.cache[code]['adv']
        else:
            adv = self._get_adv_from_ax(code)
            self.cache[code] = {'adv': adv}
            self.update_cache()
            return adv

    def _get_adv_from_ax(self, code: str) -> (float, datetime.datetime):
        from spec_equipement import build_tree
        try:
            df, tree = build_tree(code)
            ADV = df[df['code_article'].str.contains('ADV')]['code_article'].values[0]
        except Exception as e:
            print(f'Error for {code}: {e}')
            ADV = None
        return ADV

class GetBurner():

    """
    A class to get price from a code, using a cache
    """
    def __init__(self, path='./cache_bruleur.json'):
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

    def get_burner(self, code: str) -> (float, float):
        if code is None:
            return None, None
        if code in self.cache:
            return self.cache[code]['puissance'], self.cache[code]['qty']
        else:
            puissance, qty = self._get_burner_from_ax(code)
            self.cache[code] = {'puissance': puissance, 'qty': qty}
            self.update_cache()
            return puissance, qty

    def _get_burner_from_ax(self, code: str) -> (float, datetime.datetime):
        from spec_equipement import build_tree
        try:
            df, tree = build_tree(code)
            pattern = r".*?AIR.*?(\d+)KW.*"
            import re
            #  Filter rows using above pattern with regexp
            not_zero = df.loc[df['total_qty'] != 0]
            rows = not_zero[not_zero['nom_article'].str.contains(pattern)]
            #  Extract the first match
            puissance = rows['nom_article'].str.extract(pattern)[0].values[0]
            total_qty = rows['total_qty'].values[0]
            print(puissance, total_qty)

        except Exception as e:
            print(f'Error for {code}: {e}')
            puissance = None
            total_qty = None
        return puissance, total_qty

def extract_dimensions(dim_str):
    """Parse dimensions of armoire from a string"""
    none_return = pd.Series([None, None, None], index=['Length', 'Width', 'Height'])
    if pd.isna(dim_str):
        return none_return
    dim_str = dim_str.strip().lower()
    parts = dim_str.split('x')
    if len(parts) == 3:
        try:
            L, l, H = map(int, parts)
            return pd.Series([L, l, H], index=['Length', 'Width', 'Height'])
        except ValueError:
            # Handle case where conversion to int fails
            return none_return
    else:
        # Handle case where the format is not LxlxH
        return none_return

def get_armoires() -> pd.DataFrame:
    with Session() as session:
        # Read table: dimensional_ax.schema_special_plus
        df = pd.read_sql('SELECT * FROM dimensional_ax.schema_special_plus', session.bind)
        #  Fix number of motors Soufflage
        for i, row in df.iterrows():
            if pd.isna(row['MS1']):
                df.at[i, 'Nb_MS'] = 0
            elif pd.isna(row['MS2']):
                df.at[i, 'Nb_MS'] = 1
            elif pd.isna(row['MS3']):
                df.at[i, 'Nb_MS'] = 2
            elif pd.isna(row['MS4']):
                df.at[i, 'Nb_MS'] = 3

        #  Fix number of motors Extraction
        for i, row in df.iterrows():
            if pd.isna(row['ME1']):
                df.at[i, 'Nb_ME'] = 0
            elif pd.isna(row['ME2']):
                df.at[i, 'Nb_ME'] = 1
            elif pd.isna(row['ME3']):
                df.at[i, 'Nb_ME'] = 2
            elif pd.isna(row['ME4']):
                df.at[i, 'Nb_ME'] = 3

    return df

# df.to_csv('schema_special.csv', index=False)

def get_armoires_etuves(cache=True) -> pd.DataFrame:
    # Save a cache for dataframe
    if cache and os.path.exists('./cache_df_etuve.csv'):
        df_etuve = pd.read_csv('./cache_df_etuve.csv')
        return df_etuve
    df = get_armoires()

    # ETUVE
    # Filter only etuve
    df_etuve = df.loc[df['Type'] == 'ETUVE'].copy()


    # Puissance moteurs
    df_etuve['Tot_puiss_MS'] = df_etuve['MS1'].fillna(0) + df_etuve['MS2'].fillna(0)  + df_etuve['MS3'].fillna(0)  + df_etuve['MS4'].fillna(0)
    df_etuve['Tot_puiss_ME'] = df_etuve['ME1'].fillna(0)  + df_etuve['ME2'].fillna(0)  + df_etuve['ME3'].fillna(0)  + df_etuve['ME4'].fillna(0)
    df_etuve['Mean_puiss_MS'] = df_etuve['Tot_puiss_MS'] / df_etuve['Nb_MS']
    df_etuve['Mean_puiss_ME'] = df_etuve['Tot_puiss_ME'] / df_etuve['Nb_ME']




    get_price = GetPrice()




    for col in ['MS1', 'MS2', 'MS3', 'MS4', 'ME1', 'ME2', 'ME3', 'ME4']:
        # Add a demarrer column for each motor
        demarr_col = col + '_demarr'
        df_etuve[demarr_col] = df_etuve[col].apply(moteur2demarrer)

        # Add a variator column for each motor
        var_col = col + '_var'
        df_etuve[var_col] = df_etuve.apply(lambda x: var2art(x[col], x['Dem_Mot']), axis=1)

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
        df_etuve.loc[:, price_col] = df_etuve.loc[:, col].apply(lambda x: get_price.get_price(x))

    # Add price ofr each AF
    df_etuve.loc[:, "code_armoire"] = df_etuve.loc[:, "Num_AF"] + df_etuve.loc[:, "Lettrage"] + 'V1'
    df_etuve.loc[:, 'armoire_price'] = df_etuve.loc[:, "code_armoire"].apply(lambda x: get_price.get_price(x))

    #Add a totale price for MS_motor, ME_motor, demarrer, variator
    df_etuve.loc[:, 'tot_price_MS'] = df_etuve.loc[:, ['MS1_motor_price', 'MS2_motor_price', 'MS3_motor_price', 'MS4_motor_price']].sum(axis=1)
    df_etuve.loc[:, 'tot_price_ME'] = df_etuve.loc[:, ['ME1_motor_price', 'ME2_motor_price', 'ME3_motor_price', 'ME4_motor_price']].sum(axis=1)
    df_etuve.loc[:, 'tot_price_demarr'] = df_etuve.loc[:, ['MS1_demarr_price', 'MS2_demarr_price', 'MS3_demarr_price', 'MS4_demarr_price',
                                                            'ME1_demarr_price', 'ME2_demarr_price', 'ME3_demarr_price', 'ME4_demarr_price']].sum(axis=1)
    df_etuve.loc[:, 'tot_price_var'] = df_etuve.loc[:, ['MS1_var_price', 'MS2_var_price', 'MS3_var_price', 'MS4_var_price',
                                                            'ME1_var_price', 'ME2_var_price', 'ME3_var_price', 'ME4_var_price']].sum(axis=1)
    df_etuve.loc[:, 'tot_price_material'] = df_etuve.loc[:, ['tot_price_MS', 'tot_price_ME', 'tot_price_demarr', 'tot_price_var']].sum(axis=1)



    #  Add code ADV
    get_adv = GetADV()
    df_etuve.loc[:, 'ADV'] = df_etuve.loc[:, "Code_Equip"].apply(lambda x: get_adv.get_adv(x))

    #  Add code bruleur
    get_bruleur = GetBurner()
    # df_etuve.loc[:, 'puissance_bruleur'] = df_etuve.loc[:, "Code_Equip"].apply(lambda x: get_bruleur.get_burner(x))
    # Fill two columns
    df_etuve.loc[:, 'puissance_bruleur'] = df_etuve.apply(lambda x: get_bruleur.get_burner(x['Code_Equip'])[0], axis=1)
    df_etuve.loc[:, 'qty_bruleur'] = df_etuve.apply(lambda x: get_bruleur.get_burner(x['Code_Equip'])[1], axis=1)

    #  Add size armoire
    df_etuve.loc[:, ['Length', 'Width', 'Height']] = df_etuve.loc[:, 'Armoire'].apply(extract_dimensions)
    df_etuve['volume'] = df_etuve['Length'] * df_etuve['Width'] * df_etuve['Height']
    #  Fix lowercase / whitespaces
    df_etuve['Dem_Mot'] = df_etuve['Dem_Mot'].str.strip().str.lower()
    df_etuve['Chauff'] = df_etuve['Chauff'].str.strip().str.lower()
    df_etuve['Regul'] = df_etuve['Regul'].str.strip().str.lower()

    # Create a cache
    df_etuve.to_csv('./cache_df_etuve.csv', index=False)

    return df_etuve


def get_description(code_equip):
    with Session_ax() as session:
        raw_query = """
               SELECT 
               type_equip,
               description 
               FROM Entrepot_Divalto.dbo.equip_info_plus
               WHERE code_equip = :code_equip
               """
        result = session.execute(raw_query, params={
            'code_equip': code_equip
            }).fetchone()
        if result is None:
            return None, None
    return result['type_equip'], result['description']

def update_description(code_equip):
    """In table dimensional_ax.schema_special_plus, update the type_equip and description column"""
    type_equip, description = get_description(code_equip)
    with Session() as session:
        session.execute('UPDATE dimensional_ax.schema_special_plus ssp SET type_equip_divalto = :type_equip, description_divalto = :description WHERE ssp."Code_Equip" = :code_equip',
                        params={
                            'type_equip': type_equip,
                            'description': description,
                            'code_equip': code_equip
                        })
        session.commit()

def update_all_descriptions():
    # Retrieve all code_equip with no type_equip
    with Session() as session:
        raw_query = """
        SELECT 
        ssp."Code_Equip"
        FROM dimensional_ax.schema_special_plus ssp
        WHERE ssp.type_equip_divalto IS NULL
        """
        to_update = pd.read_sql(raw_query, session.bind)
    # Update each code_equip
    for i, row in to_update.iterrows():
        code_equip = row['Code_Equip']
        try:
            update_description(code_equip)
        except Exception as e:
            print(f'Error for {code_equip}: {e}')
        print(f'Updated {i} / {len(to_update)}')




if __name__ == '__main__':
    print(get_description('AF005087-D'))
    update_all_descriptions()

