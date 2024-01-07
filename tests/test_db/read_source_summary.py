import pandas as pd
path = '/Users/robertocabiecesdiaz/Documents/SurfQuake/tests/source_summary.txt'
df = pd.read_csv(path, sep = ";", na_values='missing')
#print(df)
for index, row in df.iterrows():
    #print(f'Index: {index}')
    #print(f'Row:\n{row}\n')
    lat = row['lats']
    lon = row['longs']
    date = row['date_id']
    depth = row['depths']
    Er = row['Er']
    print(lat, lon, depth,  date, Er)
    #city = row['City']