import pandas as pd
df=pd.read_csv('data/raw/15138735.csv',encoding='cp949')
print(df.shape); print(df.isna().sum())
for c in ['입차일시','출차일시']: df[c]=pd.to_datetime(df[c],errors='coerce')
print(df.describe(include='all').T)
d=(df['출차일시']-df['입차일시']).dt.total_seconds()/60
print(d.describe()); print((d<0).sum(),(d==0).sum())
df['in_h']=df['입차일시'].dt.hour; df['out_h']=df['출차일시'].dt.hour
print(df.groupby('in_h').size().to_string())
print(df.groupby('out_h').size().to_string())
daily=df.groupby(df['입차일시'].dt.date).size(); print(daily.to_string())
print(df['입차일'].unique()[:5])
