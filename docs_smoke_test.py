from epidatpy import CovidcastEpidata, EpiDataContext, EpiRange
import pandas as pd

epidata = EpiDataContext(use_cache=True, cache_max_age_days=1)
apicall = epidata.pub_covidcast(
    data_source = "fb-survey",
    signals = "smoothed_cli", 
    geo_type = "nation",
    time_type = "day",
    geo_values = "us",
    time_values = EpiRange(20210405, 20210410))
print(apicall)

pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.width', 1000)

data = apicall.df()
print(data.head())

apicall2 = epidata.pub_covidcast(
    data_source = "fb-survey",
    signals = "smoothed_cli", 
    geo_type = "state",
    time_type = "day",
    geo_values = "*",
    time_values = EpiRange(20210405, 20210410))
print(apicall2)

data2 = apicall2.df()
print(data2.head())

apicall3 = epidata.pub_covidcast(
    data_source = "fb-survey",
    signals = "smoothed_cli", 
    geo_type = "state",
    time_type = "day",
    geo_values = "pa,ca,fl",
    time_values = EpiRange(20210405, 20210410))
print(apicall3)

data3 = apicall3.df()
print(data3.head())

apicall4 = epidata.pub_covidcast(
    data_source = "fb-survey",
    signals = "smoothed_cli", 
    geo_type = "state",
    time_type = "day",
    geo_values = "pa",
    time_values = EpiRange(20210405, 20210410))
print(apicall4)

data4 = apicall4.df()
print(data4.head())

apicall5 = epidata.pub_covidcast(
    data_source = "fb-survey",
    signals = "smoothed_cli", 
    geo_type = "state",
    time_type = "day",
    geo_values = "pa",
    time_values = EpiRange(20210405, 20210410),
    as_of = "2021-06-01")
print(apicall5)

data5 = apicall5.df()
print(data5.head())

# requires matplotlib
import matplotlib.pyplot as plt

data.plot(x="time_value", y="value", title="Smoothed CLI from Facebook Survey", xlabel="Date", ylabel="CLI")
plt.subplots_adjust(bottom=.2)
plt.show()