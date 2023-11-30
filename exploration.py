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

# ETUVE
# Filter only etuve
df_etuve = df.loc[df['Type'] == 'ETUVE']


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







