import pandas as pd

df = pd.read_csv('atp_qual_chal.csv')

df = df[df["tourney_level"].astype(str).ne("C")].copy()

df = df.reset_index(drop=True)
df.to_csv("atp_qual.csv", index=False)