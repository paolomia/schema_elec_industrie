from find_best_armoire import find_best_standard
from extract_info import get_armoires_etuves, GetPrice, map_moteur, moteur2demarrer, var2art, puissance2motor, add_rotovent
import numpy as np
import matplotlib.pyplot as plt

# ETUVES MODULAIRES HT - ROTOVENTILATEURS

# ╔═╗╦═╗╔╦╗╔═╗╦╦═╗╔═╗╔═╗  ╔═╗  ╔═╗╔╗╔╔═╗╦  ╦╔═╗╔═╗╦═╗
# ╠═╣╠╦╝║║║║ ║║╠╦╝║╣ ╚═╗  ╠═╣  ╠═╣║║║╠═╣║  ║╚═╗║╣ ╠╦╝
# ╩ ╩╩╚═╩ ╩╚═╝╩╩╚═╚═╝╚═╝  ╩ ╩  ╩ ╩╝╚╝╩ ╩╩═╝╩╚═╝╚═╝╩╚═

# df_etuve = get_armoires_etuves(cache=False)
# df_etuve = df_etuve[df_etuve['type_equip_divalto'] == 'ETUVE']
# monobloc = df_etuve[(df_etuve['Chauff'].str.lower().str.strip() == 'résist élec') & (df_etuve['Nb_MS'] == 1)]
# monobloc = monobloc[~monobloc['description_divalto'].str.lower().str.contains('modul')]
# # Prend toutes les étves qui ne sont pas dans "monobloc"
# modul = df_etuve[~df_etuve['Num_AF'].isin(monobloc['Num_AF'])]
# # On elimine ces qui ont "monobloc" dans la description
# modul = modul[~modul['description_divalto'].str.lower().str.contains('monobloc')]

df_etuve = get_armoires_etuves(cache=False)
df = df_etuve[df_etuve['ADV'] == "ADV-ETUVE-MOD-HT"].copy()
# Remove variateur
df = df.loc[df['Dem_Mot'].str.lower().str.strip() != 'variateur'].copy()



# On considère le cas de 2 moteurs de soufflage et 1 moteur d'extraction
df = df.loc[(df['Nb_MS'] == 2) & (df['Nb_ME'] == 1)].copy()

#  Remove value of ME1 < 0.75
# df1 = df1.loc[df1['ME1'] >= 0.75].copy()

# REGROUPEMENT
# On prend la liste des cas unique de combinaisons d'armoires
distinct_cases = df.groupby(['ME1', 'MS1'], as_index=False)['Num_AF'].count()
# distinct_cases = distinct_cases.loc[distinct_cases['ME1'] >= 0.75].copy()

# Pour chaque cas on calcule le prix du moteur + le prix du demarreur
get_price = GetPrice()
#
# distinct_cases['MS1_motor'] = distinct_cases['MS1'].apply(lambda x: puissance2motor(x))
# distinct_cases['ME1_motor'] = distinct_cases['ME1'].apply(lambda x: puissance2motor(x))
# distinct_cases['MS1_moteur_price'] = distinct_cases['MS1_motor'].apply(lambda x: get_price.get_price(x))
# distinct_cases['ME1_moteur_price'] = distinct_cases['ME1_motor'].apply(lambda x: get_price.get_price(x))
distinct_cases['MS1_rotovent'] = distinct_cases['MS1'].apply(lambda x: add_rotovent(x))
distinct_cases['ME1_rotovent'] = distinct_cases['ME1'].apply(lambda x: add_rotovent(x))
distinct_cases['MS1_rotovent_price'] = distinct_cases['MS1_rotovent'].apply(lambda x: get_price.get_price(x))
distinct_cases['ME1_rotovent_price'] = distinct_cases['ME1_rotovent'].apply(lambda x: get_price.get_price(x))
distinct_cases['MS1_demarr'] = distinct_cases['MS1'].apply(lambda x: moteur2demarrer(x))
distinct_cases['ME1_demarr'] = distinct_cases['ME1'].apply(lambda x: moteur2demarrer(x))
distinct_cases['MS1_demarr_price'] = distinct_cases['MS1_demarr'].apply(lambda x: get_price.get_price(x))
distinct_cases['ME1_demarr_price'] = distinct_cases['ME1_demarr'].apply(lambda x: get_price.get_price(x))
# distinct_cases['tot_price'] = distinct_cases['MS1_moteur_price'] + distinct_cases['ME1_moteur_price'] + distinct_cases['MS1_demarr_price'] + distinct_cases['ME1_demarr_price']
distinct_cases['tot_price'] = 2 * distinct_cases['MS1_rotovent_price'] + distinct_cases['ME1_rotovent_price'] + 2 * distinct_cases['MS1_demarr_price'] + distinct_cases['ME1_demarr_price']

# Keep only armoire where MS1_rotovent is not None
distinct_cases = distinct_cases.loc[distinct_cases['MS1_rotovent'].isna() == False].copy()
distinct_cases = distinct_cases.loc[distinct_cases['ME1_rotovent'].isna() == False].copy()


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
        self.MS1_rotovent = add_rotovent(MS1)
        self.ME1_rotovent = add_rotovent(ME1)
        self.MS1_rotovent_price = get_price.get_price(self.MS1_rotovent) * 2
        self.ME1_rotovent_price = get_price.get_price(self.ME1_rotovent)
        self.MS1_demarr = moteur2demarrer(MS1)
        self.ME1_demarr = moteur2demarrer(ME1)
        self.MS1_demarr_price = get_price.get_price(self.MS1_demarr) * 2
        self.ME1_demarr_price = get_price.get_price(self.ME1_demarr)
        self.tot_price = self.MS1_rotovent_price + self.ME1_rotovent_price + self.MS1_demarr_price + self.ME1_demarr_price

        def can_replace(old_MS, old_ME, old_price, new_MS, new_ME, new_price):
            """Return True if the new armoire can replace the old one"""
            if (old_MS > new_MS) | (old_ME > new_ME):
                return False
            if (old_MS <= 4) and (new_MS > 4):
                return False
            if new_price - old_price > 300:
                return False
            # if old_MS != new_MS:
            #     return False
            return True
        # DEFINITION DU MASQUE
        # A numpy array of boolean, where True means that the line can be replaced by this armoire
        # self.mask = ((df['MS1'] <= self.MS1) & (df['ME1'] <= self.ME1)).values
        self.mask = [can_replace(old_MS, old_ME, old_price, self.MS1, self.ME1, self.tot_price) for old_MS, old_ME, old_price in zip(df['MS1'], df['ME1'], df['tot_price'])]

        self.mask = np.array(self.mask, dtype=np.float32)

    def price(self):
        return self.tot_price


all_armoires = [Armoire(MS1, ME1, distinct_cases) for MS1, ME1 in zip(distinct_cases['MS1'], distinct_cases['ME1'])]

# Round the prices to the nearest integer for faster computation
arm_prices = np.array([armoire.price() for armoire in all_armoires], dtype=np.float32)
arm_numb = np.array(distinct_cases['Num_AF'], dtype=np.float32)
arm_tot_price = arm_prices * arm_numb

#  Find best standard
find_best_standard(n_standard=3, all_armoires=all_armoires, arm_numb=arm_numb, arm_tot_price=arm_tot_price, label='3_stand_HT_rotovent_cheap')