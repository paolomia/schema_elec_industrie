import pandas as pd
from extract_info import get_armoires_etuves, GetPrice, map_moteur, moteur2demarrer, var2art, puissance2motor
from tqdm import tqdm



df = get_armoires_etuves(cache=False)

# On considère d'abord le cas avec un seul moteur soufflage et extraction
df1 = df.loc[(df['Nb_MS'] == 1) & (df['Nb_ME'] == 1)].copy()

# On considère le cas où il n'y a pas de variateur
df1 = df1.loc[(df1['Dem_Mot'].str.lower() == 'direct')].copy()
df1

# On ignore la partie resistence et régulateur



get_price = GetPrice()
cache = {}
# On prende chaque combination de moteurs et on regarde le cout et l'écart par rapport à tous les armoires concernées
for MS1_standard in tqdm(map_moteur):
    for ME1_standard in map_moteur:

        #  On calcule le prix de l'armoire
        prix = get_price.get_price(MS1_standard['code']) + get_price.get_price(ME1_standard['code'])

        # On complète l'armoire (pas necessaire car basses puissances)
        # MS1_dem = moteur2demarrer(MS1_standard['min'])
        # ME1_dem = moteur2demarrer(ME1_standard['min'])
        # prix += get_price.get_price(MS1_dem) + get_price.get_price(ME1_dem)

        # On filtre dans le dataframe les armoires avec puissance inférieure à la puissance standard
        df1_remplace = df1.loc[(df1['MS1'] <= MS1_standard['max']) & (df1['ME1'] <= ME1_standard['max'])].copy()
        n_remplace = len(df1_remplace)
        # On calcule le cout moyen de ces moteurs/ demarreurs
        mean_price = df1_remplace['tot_price_MS'].mean() + df1_remplace['tot_price_ME'].mean()  + \
                     df1_remplace['tot_price_demarr'].mean()
        # On calcule l'écart
        ecart = prix - mean_price
        # On ajoute l'information dans le cache
        cache[(MS1_standard['code'], ME1_standard['code'])] = (prix, ecart, n_remplace)
print(cache)
# Make a x-y scatter plot using cache where x =n_remplace and y = ecart
x = []
y = []
import matplotlib.pyplot as plt
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
for key, value in cache.items():
    x.append(value[2]/len(df1))
    y.append(value[1])
plt.scatter(x, y)
#  Add grid
plt.grid()
plt.show()

# On repete la même chose avec deux standards moteurs

get_price = GetPrice()
cache = []

from numba import jit

# @jit
def simulate_case(MS1_standard_idx, ME1_standard_idx, MS1_standard_2_idx, ME1_standard_2_idx):
    map_moteur = [# {"min": 0.75, "max": 0.75, "code": "KU07 31"},
        #     Je ne trouve pas de standard < 0.75 donc je prends le plus proche
        {
            "min": 0,
            "max": 0.75,
            'power': 0.75,
            "code": "KU07 32"
            }, {
            "min": 1.1,
            "max": 1.1,
            'power': 1.1,
            "code": "KU07 30"
            }, {
            "min": 1.5,
            "max": 1.5,
            'power': 1.5,
            "code": "KU07 24"
            }, {
            "min": 2.2,
            "max": 2.2,
            'power': 2.2,
            "code": "KU07 25"
            }, {
            "min": 3.0,
            "max": 3.0,
            'power': 3.0,
            "code": "KU07 26"
            }, {
            "min": 4.0,
            "max": 4.0,
            'power': 4.0,
            "code": "KU07 27"
            }, {
            "min": 5.5,
            "max": 5.5,
            'power': 5.5,
            "code": "KU07 28"
            }, {
            "min": 7.5,
            "max": 7.5,
            'power': 7.5,
            "code": "KU08 21"
            }, {
            "min": 9.0,
            "max": 9.0,
            'power': 9,
            "code": "KU08 3"
            }, {
            "min": 9.2,
            "max": 9.2,
            'power': 9.2,
            "code": "KU08 44"
            }, {
            "min": 11,
            "max": 11,
            'power': 11,
            "code": "KU08 25"
            }, {
            "min": 15,
            "max": 15,
            'power': 15,
            "code": "KU08 26"
            }, {
            "min": 18.5,
            "max": 18.5,
            'power': 18.5,
            "code": "KU08 27"
            }, {
            "min": 22,
            "max": 22,
            'power': 22,
            "code": "KU08 28"
            },

        ]
    MS1_standard = map_moteur[MS1_standard_idx]
    ME1_standard = map_moteur[ME1_standard_idx]
    MS1_standard_2 = map_moteur[MS1_standard_2_idx]
    ME1_standard_2 = map_moteur[ME1_standard_2_idx]
    # On calcule le prix de l'armoire
    prix_1 = get_price.get_price(MS1_standard['code']) + get_price.get_price(ME1_standard['code'])
    prix_2 = get_price.get_price(MS1_standard_2['code']) + get_price.get_price(ME1_standard_2['code'])
    # On complète l'armoire
    MS1_dem = moteur2demarrer(MS1_standard['min'])
    ME1_dem = moteur2demarrer(ME1_standard['min'])
    MS1_dem_2 = moteur2demarrer(MS1_standard_2['min'])
    ME1_dem_2 = moteur2demarrer(ME1_standard_2['min'])
    prix_1 += get_price.get_price(MS1_dem) + get_price.get_price(ME1_dem)
    prix_2 += get_price.get_price(MS1_dem_2) + get_price.get_price(ME1_dem_2)

    #  On prend le moins cher des deux
    MS_cheap = MS1_standard if prix_1 < prix_2 else MS1_standard_2
    ME_cheap = ME1_standard if prix_1 < prix_2 else ME1_standard_2

    MS_expensive = MS1_standard if prix_1 > prix_2 else MS1_standard_2
    ME_expensive = ME1_standard if prix_1 > prix_2 else ME1_standard_2

    prix_cheap = prix_1 if prix_1 < prix_2 else prix_2
    prix_expensive = prix_1 if prix_1 > prix_2 else prix_2

    # On filtre dans le dataframe les armoires avec puissance inférieure à la puissance du cheap
    df1_remplace_cheap = df1.loc[(df1['MS1'] <= MS_cheap['max']) & (df1['ME1'] <= ME_cheap['max'])].copy()
    n_remplace_cheap = len(df1_remplace_cheap)
    # On calcule le cout moyen de ces moteurs/ demarreurs
    mean_price = df1_remplace_cheap['tot_price_MS'].mean() + df1_remplace_cheap['tot_price_ME'].mean() + df1_remplace_cheap['tot_price_demarr'].mean()
    # On calcule l'écart avec le prix du cheap
    ecart_cheap = prix_cheap - mean_price

    # Dans ce qui n'est pas remplacé par le cheap, on regarde si on peut remplacer par le expensive
    df1_remplace_expensive = df1.loc[(df1['MS1'] <= MS_expensive['max']) & (df1['ME1'] <= ME_expensive['max'])].copy()
    df1_remplace_expensive = df1_remplace_expensive.loc[(df1_remplace_expensive['MS1'] > MS_cheap['max']) | (df1_remplace_expensive['ME1'] > ME_cheap['max'])].copy()
    n_remplace_expensive = len(df1_remplace_expensive)

    # On calcule le cout moyen de ces moteurs/ demarreurs
    mean_price = df1_remplace_expensive['tot_price_MS'].mean() + df1_remplace_expensive['tot_price_ME'].mean() + df1_remplace_expensive['tot_price_demarr'].mean()
    # On calcule l'écart avec le prix du expensive
    ecart_exp = prix_expensive - mean_price

    # On calcule l'écart total
    n_remplace = n_remplace_cheap + n_remplace_expensive
    ecart = (ecart_cheap * n_remplace_cheap + ecart_exp * n_remplace_expensive) / n_remplace

    # Return as a tuple
    return (MS_cheap['code'], ME_cheap['code'], MS_expensive['code'], ME_expensive['code'], prix_cheap, prix_expensive, ecart, n_remplace, MS_cheap['power'], ME_cheap['power'], MS_expensive['power'], ME_expensive['power'])

# On prende chaque combination de moteurs et on regarde le cout et l'écart par rapport à tous les armoires concernées
for MS1_standard_idx, MS1_standard in enumerate(tqdm(map_moteur)):
    for ME1_standard_idx, ME1_standard in enumerate(map_moteur):
        for MS1_standard_2_idx, MS1_standard_2 in enumerate(map_moteur):
            for ME1_standard_2_idx, ME1_standard_2 in enumerate(map_moteur):
                res = simulate_case(MS1_standard_idx, ME1_standard_idx, MS1_standard_2_idx, ME1_standard_2_idx)
                # Convert to dict
                res_dict = {
                    'MS_cheap': res[0],
                    'ME_cheap': res[1],
                    'MS_expensive': res[2],
                    'ME_expensive': res[3],
                    'prix_cheap': res[4],
                    'prix_expensive': res[5],
                    'ecart': res[6],
                    'n_remplace': res[7],
                    'MS_cheap_power': res[8],
                    'ME_cheap_power': res[9],
                    'MS_expensive_power': res[10],
                    'ME_expensive_power': res[11],
                    }
                cache.append(res_dict)


# COnvert le cache en dataframe
df_cache = pd.DataFrame(cache)
df_cache.reset_index(inplace=True)
#  Save cache
df_cache.to_csv('./cache_df_cache.csv', index=False)