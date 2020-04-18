import tabula
import glob
import pandas as pd

''' Extract the crime information from each district table for each report'''

filenames = glob.glob('../raw_data/*.pdf')

tables = []
for filename in filenames:
    dfs = tabula.read_pdf(filename, pages='all',multiple_tables=True,guess=True)
    for df in dfs:
        if 'CASE#' in df.columns:
            tables.append(df)
        elif 'CASE_NUM' in df.columns:
            tables.append(df)
        elif 'CASE' in df.columns:
            tables.append(df)
        elif 'CASE_NU' in df.columns:
            tables.append(df)
        elif 'CASE_#' in df.columns:
            tables.append(df)

df = pd.concat(tables)
df.reset_index(drop=True,inplace=True)
df.to_csv('crime_data_uncleaned.csv')
