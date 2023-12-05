import pandas as pd
import openpyxl
import os
import urllib
import datetime
from db_utils.base import Session, Session_ax
import matplotlib.pyplot as plt
import seaborn as sns
from extract_info import get_armoires_etuves, GetPrice, moteur2demarrer, var2art, map_moteur
from tqdm import tqdm

with Session() as session:
    # Read table: dimensional_ax.schema_special_plus
    df = pd.read_sql('SELECT * FROM dimensional_ax.schema_special_plus', session.bind)

# df.to_csv('schema_special.csv', index=False)

#  DISTRIBUTION EQUIPMENTS
types = df['Type']
# Count the number of each type
types_count = types.groupby(types).count()
# Sort values
types_count.sort_values(inplace=True, ascending=False)
# Keep only the first 10
types_count = types_count[:10]
# Plot
plt.figure(figsize=(9, 6))
plt.bar(types_count.index, types_count.values)
plt.title("Distribution équipements")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


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





# ETUVE
# Filter only etuve
df_etuve = df.loc[df['Type'] == 'ETUVE'].copy()


# NOMBRE DE MOTEURS
# Plot Nb_MS distribution
fig, ax = plt.subplots(1, 1, figsize=(9, 6))

# Calculate frequencies for column Nb_MS
freq_MS = df_etuve['Nb_MS'].value_counts()
freq_ME = df_etuve['Nb_ME'].value_counts()


# Put distribution of Nb_MS and Nb_ME side by side. Same width, use an offset
plt.bar(freq_MS.index - 0.2, freq_MS.values, width=0.4, label='Soufflage')
plt.bar(freq_ME.index + 0.2, freq_ME.values, width=0.4, label='Extraction')
plt.title("Nombre de moteurs - Etuves")
plt.legend()
plt.tight_layout()
plt.show()

# Puissance moteurs
df_etuve['Tot_puiss_MS'] = df_etuve['MS1'].fillna(0) + df_etuve['MS2'].fillna(0)  + df_etuve['MS3'].fillna(0)  + df_etuve['MS4'].fillna(0)
df_etuve['Tot_puiss_ME'] = df_etuve['ME1'].fillna(0)  + df_etuve['ME2'].fillna(0)  + df_etuve['ME3'].fillna(0)  + df_etuve['ME4'].fillna(0)
df_etuve['Mean_puiss_MS'] = df_etuve['Tot_puiss_MS'] / df_etuve['Nb_MS']
df_etuve['Mean_puiss_ME'] = df_etuve['Tot_puiss_ME'] / df_etuve['Nb_ME']

# Make a boxplot for MS and ME (share x axis)
fig, ax = plt.subplots(2, 1, figsize=(9, 10), sharex=True)
sns.boxplot(y=df_etuve['Mean_puiss_MS'], ax=ax[0], x=df_etuve['Nb_MS'])
ax[0].set_title("Puissance moyenne moteurs soufflage")
sns.boxplot(y=df_etuve['Mean_puiss_ME'], ax=ax[1], x=df_etuve['Nb_ME'])
ax[1].set_title("Puissance moyenne moteurs extraction")
plt.tight_layout()
plt.show()



get_price = GetPrice()

#  Plot motors prices as scatter X=power, Y=price
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
x = [ motor['power'] for motor in map_moteur]
y = [ get_price.get_price(motor['code']) for motor in map_moteur]
y_demarr = [ get_price.get_price(motor['code']) + get_price.get_price(moteur2demarrer(motor['power'])) for motor in map_moteur]
ax.scatter(x, y, label='Prix Moteur', color='red', marker='x')
ax.scatter(x, y_demarr, label='Prix Moteur + Demarrer', color='blue', marker='o')

#  add a simple linear regression line for y_demarr
import numpy as np
from scipy.stats import linregress
slope, intercept, r_value, p_value, std_err = linregress(x, y_demarr)
x_line = np.linspace(0, max(x), 100)
y_line = slope * x_line + intercept
ax.plot(x_line, y_line, label='Regression', color='green')


plt.xlabel('Puissance moteur (kW)')
plt.ylabel('Prix (€)')
plt.legend()
# Add grid
plt.grid()
#  Show rounded equation of regression line by adding a text box
#  https://stackoverflow.com/questions/15910019/annotate-data-points-while-plotting-from-pandas-dataframe
text = "y = {:.1f}x + {:.0f}".format(slope, intercept)
props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
ax.text(0.05, 0.8, text, transform=ax.transAxes, fontsize=14,
        verticalalignment='top', bbox=props)


plt.title('Prix moteurs en fonction de la puissance')
plt.tight_layout()
#  Save figure in ./plots
plt.savefig('./plots/price_motor.png')
plt.show()

# DISTRIBUTION PUISSANCE MOTEURS
df_etuve = get_armoires_etuves(cache=False)
df1 = df_etuve.loc[(df_etuve['Nb_MS'] == 1) & (df_etuve['Nb_ME'] == 1)].copy()

#  Make a bubble plot using df1 where x = puissance soufflage, y = puissance extraction, size = nb armoires
distinct_cases = df1.groupby(['MS1', 'ME1'], as_index=False)['Num_AF'].count()
# Add number of armoires as text on each bubble
distinct_cases['text'] = distinct_cases['Num_AF'].apply(lambda x: str(x))


#  Plot
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
ax.scatter(distinct_cases['MS1'], distinct_cases['ME1'], s=distinct_cases['Num_AF']*10)
# Add text
for i, txt in enumerate(distinct_cases['text']):
    ax.annotate(txt, (distinct_cases['MS1'].iloc[i], distinct_cases['ME1'].iloc[i]))
plt.xlabel('Puissance soufflage (kW)')
plt.ylabel('Puissance extraction (kW)')
plt.title('Distribution des puissances moteurs- pour les étuves Nb_MS=1, Nb_ME=1')
plt.tight_layout()
#  Save figure in ./plots
plt.savefig('./plots/distribution_puissances.png')
plt.show()

# DISTRIBUTION NOMBRE DE MOTEURS
# Make a bubble plot using df_etuve where x= Nb_MS, y = Nb_ME, size = nb armoires
distinct_cases = df_etuve.groupby(['Nb_MS', 'Nb_ME'], as_index=False)['Num_AF'].count()
#  Plot
fig, ax = plt.subplots(1, 1, figsize=(9, 6))
ax.scatter(distinct_cases['Nb_MS'], distinct_cases['Nb_ME'], s=distinct_cases['Num_AF']*10)
plt.xlabel('Nombre de moteurs soufflage')
plt.ylabel('Nombre de moteurs extraction')
plt.title('Distribution des nombres de moteurs - pour les étuves')
plt.tight_layout()
#  Save figure in ./plots
plt.savefig('./plots/distribution_nb_moteurs.png')
plt.show()

