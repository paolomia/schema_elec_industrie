from find_best_armoire import find_best_standard
from extract_info import get_armoires_etuves, GetPrice, map_moteur, moteur2demarrer, var2art, puissance2motor
import numpy as np
import matplotlib.pyplot as plt

# ETUVES MODULAIRES

# ╔═╗╦═╗╔╦╗╔═╗╦╦═╗╔═╗╔═╗  ╔═╗  ╔═╗╔╗╔╔═╗╦  ╦╔═╗╔═╗╦═╗
# ╠═╣╠╦╝║║║║ ║║╠╦╝║╣ ╚═╗  ╠═╣  ╠═╣║║║╠═╣║  ║╚═╗║╣ ╠╦╝
# ╩ ╩╩╚═╩ ╩╚═╝╩╩╚═╚═╝╚═╝  ╩ ╩  ╩ ╩╝╚╝╩ ╩╩═╝╩╚═╝╚═╝╩╚═

df_etuve = get_armoires_etuves(cache=False)
df_etuve = df_etuve[df_etuve['type_equip_divalto'] == 'ETUVE']
monobloc = df_etuve[(df_etuve['Chauff'].str.lower().str.strip() == 'résist élec') & (df_etuve['Nb_MS'] == 1)]
monobloc = monobloc[~monobloc['description_divalto'].str.lower().str.contains('modul')]
# Prend toutes les étves qui ne sont pas dans "monobloc"
modul = df_etuve[~df_etuve['Num_AF'].isin(monobloc['Num_AF'])]
# On elimine ces qui ont "monobloc" dans la description
modul = modul[~modul['description_divalto'].str.lower().str.contains('monobloc')]



# On considère d'abord le cas avec un seul moteur soufflage et extraction
df1 = modul.loc[(modul['Nb_MS'] == 2) & (modul['Nb_ME'] == 1)].copy()

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
distinct_cases['tot_price'] = distinct_cases['MS1_moteur_price'] + distinct_cases['ME1_moteur_price'] + distinct_cases['MS1_demarr_price'] + distinct_cases['ME1_demarr_price']

# Sort by tot_price
distinct_cases.sort_values(by='tot_price', inplace=True)


#  Plot
distinct_cases['text'] = distinct_cases['Num_AF'].apply(lambda x: str(x))
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
ax.scatter(distinct_cases['MS1'], distinct_cases['ME1'], s=distinct_cases['Num_AF']*50, color='orange', alpha=0.5)
# Add text
for i, txt in enumerate(distinct_cases['text']):
    # Center text horizontally and vertically.
    ax.text(distinct_cases['MS1'].iloc[i], distinct_cases['ME1'].iloc[i], txt, ha='center', va='center', color='black')

plt.xlabel('Puissance soufflage (kW)')
plt.ylabel('Puissance extraction (kW)')
tot_mono = distinct_cases['Num_AF'].sum()
plt.title(f'Distribution des puissances moteurs (TOT: {tot_mono})')
plt.tight_layout()
plt.show()


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
find_best_standard(n_standard=2, all_armoires=all_armoires, arm_numb=arm_numb, arm_tot_price=arm_tot_price, label='1_standard')