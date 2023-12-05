import pandas as pd
from extract_info import get_armoires_etuves, GetPrice, map_moteur, moteur2demarrer, var2art, puissance2motor
from tqdm import tqdm
import numpy as np
from itertools import combinations
import numba
import datetime






# ╦═╗╔═╗╔═╗╦ ╦╔═╗╦═╗╔═╗╦ ╦╔═╗  ╔═╗╔╦╗╔═╗╔╗╔╔╦╗╔═╗╦═╗╔╦╗
# ╠╦╝║╣ ║  ╠═╣║╣ ╠╦╝║  ╠═╣║╣   ╚═╗ ║ ╠═╣║║║ ║║╠═╣╠╦╝ ║║
# ╩╚═╚═╝╚═╝╩ ╩╚═╝╩╚═╚═╝╩ ╩╚═╝  ╚═╝ ╩ ╩ ╩╝╚╝═╩╝╩ ╩╩╚══╩╝



# @numba.jit(nopython=True)
def calculate(M_list, P_list, arm_numb, arm_tot_price):
    n_remplace = 0
    ecart_tot = 0
    for Mj, Pj in zip(M_list, P_list):
        n_remplace_j = np.dot(Mj, arm_numb)
        n_remplace += n_remplace_j
        ecart_tot += n_remplace_j * Pj - np.dot(Mj, arm_tot_price)
    ecart = ecart_tot / n_remplace
    return n_remplace, ecart


def find_best_standard(n_standard, all_armoires, arm_numb, arm_tot_price, label=None):

    #  If label is None, we use a datetime string
    if label is None:
        label = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    cache = []
    # Take all pairs of armoires

    nombre_armoires = int(np.sum(arm_numb))

    for A_list in combinations(all_armoires, n_standard):
        P_list = [A.price() for A in A_list]
        M_list = [A_list[0].mask]
        for A in A_list[1:]:
            M_list.append(A.mask * (1 - M_list[0]))

        n_remplace, ecart = calculate(M_list, P_list, arm_numb, arm_tot_price)
        spec_armoire = [A.MS1 for A in A_list] + [A.ME1 for A in A_list]

        cache.append([int(n_remplace), int(100*n_remplace/nombre_armoires), int(ecart)] + spec_armoire)

    df = pd.DataFrame(cache, columns=['n_remplace', '% Remp', 'ecart'] + [f'MS{i+1} kW' for i in range(n_standard)] + [f'ME{i+1} kW' for i in range(n_standard)])

    best_results = []

    last_best_ecart = 100000
    for n_remp in range(nombre_armoires, 0, -1):
        # Find the best armoire for n_remp
        df_n_remp = df.loc[df['n_remplace'] == n_remp]
        if len(df_n_remp) == 0:
            continue
        # Find the row with lowest ecart
        idx_min = df_n_remp['ecart'].idxmin()
        if df_n_remp.loc[idx_min, 'ecart'] >= last_best_ecart:
            continue
        best_results.append(df_n_remp.loc[idx_min])
        last_best_ecart = df_n_remp.loc[idx_min, 'ecart']

    df_best = pd.DataFrame(best_results)
    df_best.sort_values(by='n_remplace', inplace=True)
    df_best.reset_index(inplace=True)
    df_best.drop(columns=['index'], inplace=True)



    # df.to_csv('./cache_df_' + label + '.csv', index=False)
    df_best.to_csv('./best_results_' + label + '.csv', index=False)
    # Plot n_remplace vs ecart for best results
    import matplotlib.pyplot as plt
    plt.scatter(df_best['n_remplace'], df_best['ecart'])
    plt.xlabel('Nombre d\'armoires remplacées')
    plt.ylabel('Ecart prix moyen (€)')
    plt.grid()
    plt.show()


# JIT, float32: 10.56 it/s
# No JIT, float32: 1.9 it/s
# No JIT, uint8: 2.8 it/s

if __name__ == '__main__':



    # ╔═╗╦═╗╔╦╗╔═╗╦╦═╗╔═╗╔═╗  ╔═╗  ╔═╗╔╗╔╔═╗╦  ╦╔═╗╔═╗╦═╗
    # ╠═╣╠╦╝║║║║ ║║╠╦╝║╣ ╚═╗  ╠═╣  ╠═╣║║║╠═╣║  ║╚═╗║╣ ╠╦╝
    # ╩ ╩╩╚═╩ ╩╚═╝╩╩╚═╚═╝╚═╝  ╩ ╩  ╩ ╩╝╚╝╩ ╩╩═╝╩╚═╝╚═╝╩╚═

    df = get_armoires_etuves(cache=False)
    print(df)

    # On considère d'abord le cas avec un seul moteur soufflage et extraction
    df1 = df.loc[(df['Nb_MS'] == 1) & (df['Nb_ME'] == 1)].copy()

    #  Remove value of ME1 < 0.75
    df1 = df1.loc[df1['ME1'] >= 0.75].copy()

    # REGROUPEMENT
    # On prend la liste des cas unique de combinaisons d'armoires
    distinct_cases = df1.groupby(['ME1', 'MS1'], as_index=False)['Num_AF'].count()
    # distinct_cases = distinct_cases.loc[distinct_cases['ME1'] >= 0.75].copy()

    # Pour chaque cas on calcule le prix du moteur + le prix du demarreur
    get_price = GetPrice()

    distinct_cases['MS1_motor'] = distinct_cases['MS1'].apply(lambda x: puissance2motor(x))
    distinct_cases['ME1_motor'] = distinct_cases['ME1'].apply(lambda x: puissance2motor(x))
    distinct_cases['MS1_moteur_price'] = distinct_cases['MS1_motor'].apply(lambda x: get_price.get_price(x))
    distinct_cases['ME1_moteur_price'] = distinct_cases['ME1_motor'].apply(lambda x: get_price.get_price(x))
    distinct_cases['MS1_demarr'] = distinct_cases['MS1'].apply(lambda x: moteur2demarrer(x))
    distinct_cases['ME1_demarr'] = distinct_cases['ME1'].apply(lambda x: moteur2demarrer(x))
    distinct_cases['MS1_demarr_price'] = distinct_cases['MS1_demarr'].apply(lambda x: get_price.get_price(x))
    distinct_cases['ME1_demarr_price'] = distinct_cases['ME1_demarr'].apply(lambda x: get_price.get_price(x))
    distinct_cases['tot_price'] = distinct_cases['MS1_moteur_price'] + distinct_cases['ME1_moteur_price'] + \
                                  distinct_cases['MS1_demarr_price'] + distinct_cases['ME1_demarr_price']

    # Sort by tot_price
    distinct_cases.sort_values(by='tot_price', inplace=True)
    print(distinct_cases)


    # ╔═╗╦═╗╔═╗╔═╗╔═╗╔═╗╦╔╦╗╦╔═╗╔╗╔  ╔═╗╔╦╗╔═╗╔╗╔╔╦╗╔═╗╦═╗╔╦╗
    # ╠═╝╠╦╝║ ║╠═╝║ ║╚═╗║ ║ ║║ ║║║║  ╚═╗ ║ ╠═╣║║║ ║║╠═╣╠╦╝ ║║
    # ╩  ╩╚═╚═╝╩  ╚═╝╚═╝╩ ╩ ╩╚═╝╝╚╝  ╚═╝ ╩ ╩ ╩╝╚╝═╩╝╩ ╩╩╚══╩╝

    class Armoire:
        def __init__(self, MS1, ME1, df):
            self.MS1 = MS1
            self.ME1 = ME1
            self.MS1_motor = puissance2motor(MS1)
            self.ME1_motor = puissance2motor(ME1)
            self.MS1_moteur_price = get_price.get_price(self.MS1_motor)
            self.ME1_moteur_price = get_price.get_price(self.ME1_motor)
            self.MS1_demarr = moteur2demarrer(MS1)
            self.ME1_demarr = moteur2demarrer(ME1)
            self.MS1_demarr_price = get_price.get_price(self.MS1_demarr)
            self.ME1_demarr_price = get_price.get_price(self.ME1_demarr)
            self.tot_price = self.MS1_moteur_price + self.ME1_moteur_price + self.MS1_demarr_price + self.ME1_demarr_price

            # DEFINITION DU MASQUE
            # A numpy array of boolean, where True means that the line can be replaced by this armoire
            self.mask = ((df['MS1'] <= self.MS1) & (df['ME1'] <= self.ME1)).values
            self.mask = np.array(self.mask, dtype=np.float32)

        def price(self):
            return self.tot_price


    all_armoires = [Armoire(MS1, ME1, distinct_cases) for MS1, ME1 in zip(distinct_cases['MS1'], distinct_cases['ME1'])]

    # Round the prices to the nearest integer for faster computation
    arm_prices = np.array([armoire.price() for armoire in all_armoires], dtype=np.float32)
    arm_numb = np.array(distinct_cases['Num_AF'], dtype=np.float32)
    arm_tot_price = arm_prices * arm_numb


    #  Find best standard
    find_best_standard(n_standard=1, all_armoires=all_armoires, arm_numb=arm_numb, arm_tot_price=arm_tot_price, label='1_standard')