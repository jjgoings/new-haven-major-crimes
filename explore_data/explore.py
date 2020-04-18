import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('../clean_data/crime_data_clean.csv')
df['CASE_NUMBER'] = df['CASE_NUMBER'].astype('Int64')
df['DISTRICT'] = df['DISTRICT'].astype('Int64')
df['DATETIME'] = pd.to_datetime(df['DATETIME'])

def line_format(label):
    """
    Convert time label to the format of pandas line plot
    """
    month = label.month_name()[:3]
    if month == 'Jan':
        month += f'\n{label.year}'
    elif month == 'Jul':
        month += f'\n{label.year}'
    return month

df.index = df.DATETIME
week = df.groupby(['CHRG_DESC'])['CHRG_DESC'].resample('M').count()
burglary = week.BURGLARY
ax = burglary.plot(kind='bar')
plt.title('Burglaries per month in New Haven between Jul 1 2019 and Apr 12 2020')
plt.ylabel('Number burglaries')
plt.xlabel('Month')
ax.set_xticklabels(map(lambda x: line_format(x), burglary.index))
plt.show()
