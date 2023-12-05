import pandas as pd
from extract_info import get_armoires_etuves, GetPrice, map_moteur, moteur2demarrer, var2art, puissance2motor
from tqdm import tqdm
import json
import matplotlib.pyplot as plt


csv_path = './cache_df_cache.csv'

df = get_armoires_etuves(cache=False)
print(df)

# On considère d'abord le cas avec un seul moteur soufflage et extraction
df1 = df.loc[(df['Nb_MS'] == 1) & (df['Nb_ME'] == 1)].copy()

df_sol = pd.read_csv('./cache_df_cache.csv')

# Make a groupby, to extract for each value of n_remplace,
# the line where ecart is minimum

df_best_sol_ecart = df_sol.groupby('n_remplace', as_index=False)['ecart'].min()
#  Filter NaN values
df_best_sol_ecart = df_best_sol_ecart.loc[~pd.isna(df_best_sol_ecart['ecart'])].copy()
# Filter only the best solutions using a merge
df_best_sol = pd.merge(df_sol, df_best_sol_ecart, on=['n_remplace', 'ecart'], how='inner')


#  Take a proposed solution
sol = df_best_sol.iloc[8]

MS_cheap_power = sol['MS_cheap_power']
ME_cheap_power = sol['ME_cheap_power']
MS_expensive_power = sol['MS_expensive_power']
ME_expensive_power = sol['ME_expensive_power']


#  PLOT DISTRIBUTION OF MOTOR POWER
df_etuve = get_armoires_etuves(cache=False)
df1 = df_etuve.loc[(df_etuve['Nb_MS'] == 1) & (df_etuve['Nb_ME'] == 1)].copy()



#  Make a bubble plot using df1 where x = puissance soufflage, y = puissance extraction, size = nb armoires
distinct_cases = df1.groupby(['MS1', 'ME1'], as_index=False)['Num_AF'].count()
#  Plot
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
ax.scatter(distinct_cases['MS1'], distinct_cases['ME1'], s=distinct_cases['Num_AF']*10)

# Plot proposed solutions as points
ax.scatter(MS_cheap_power, ME_cheap_power, s=100, color='red', marker='x')
ax.scatter(MS_expensive_power, ME_expensive_power, s=100, color='red', marker='x')

plt.xlabel('Puissance soufflage (kW)')
plt.ylabel('Puissance extraction (kW)')
plt.title('Distribution des puissances moteurs- pour les étuves Nb_MS=1, Nb_ME=1')
plt.tight_layout()
#  Save figure in ./plots
plt.savefig('./plots/sol.png')
plt.show()