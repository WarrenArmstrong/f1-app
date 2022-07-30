# %%
import pandas as pd
import plotly.express as px
import itertools as it
# %%
df = pd.read_csv('data/constructor_color.csv')
df['auto_color'] = list(it.islice(it.cycle(px.colors.qualitative.Dark24), df.shape[0]))

df
# %%
df.to_csv('data/constructor_color.csv', index=False)
# %%
