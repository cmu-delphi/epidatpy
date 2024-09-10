from epidatpy import EpiDataContext, EpiRange
import matplotlib.pyplot as plt
import pandas as pd

# Set common options and context

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

epidata = EpiDataContext(use_cache=True, cache_max_age_days=1)

# Getting started with epidatpy

apicall = epidata.pub_covidcast(
    data_source = "fb-survey",
    signals = "smoothed_cli", 
    geo_type = "nation",
    time_type = "day",
    geo_values = "us",
    time_values = EpiRange(20210405, 20210410))
print(apicall)

data = apicall.df()

data.plot(x="time_value", y="value", title="Smoothed CLI from Facebook Survey", xlabel="Date", ylabel="CLI")
plt.subplots_adjust(bottom=.2)
plt.show()
