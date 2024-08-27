from epidatpy import CovidcastEpidata, EpiDataContext, EpiRange
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

# Signal discovery

epidata2 = CovidcastEpidata()
sources = epidata2.source_df
print(sources.head())

signals = epidata2.signal_df
print(signals.head())

# Versioned data

apicall6 = epidata.pub_covidcast(
    data_source = "doctor-visits",
    signals = "smoothed_cli", 
    time_type = "day",
    time_values = EpiRange("2020-05-01", "2020-05-01"),
    geo_type = "state",
    geo_values = "pa",
    as_of = "2020-05-07"
)
print(apicall6)

data6 = apicall6.df()
print(data6.head())

apicall7 = epidata.pub_covidcast(
    data_source = "doctor-visits",
    signals = "smoothed_cli", 
    time_type = "day",
    time_values = EpiRange("2020-05-01", "2020-05-01"),
    geo_type = "state",
    geo_values = "pa"
)
print(apicall7)

data7 = apicall7.df()
print(data7.head())

apicall8 = epidata.pub_covidcast(
    data_source = "doctor-visits",
    signals = "smoothed_adj_cli",
    time_type = "day",
    time_values = EpiRange("2020-05-01", "2020-05-01"),
    geo_type = "state",
    geo_values = "pa",
    issues = EpiRange("2020-05-01", "2020-05-15")
)
print(apicall8)

data8 = apicall8.df()
print(data8.head(7))

apicall9 = epidata.pub_covidcast(
    data_source = "doctor-visits",
    signals = "smoothed_adj_cli",
    time_type = "day",
    time_values = EpiRange("2020-05-01", "2020-05-07"),
    geo_type = "state",
    geo_values = "pa",
    lag = 7
)
print(apicall9)

data9 = apicall9.df()
print(data9.head())

apicall10 = epidata.pub_covidcast(
    data_source = "doctor-visits",
    signals = "smoothed_adj_cli",
    time_type = "day",
    time_values = EpiRange("2020-05-03", "2020-05-03"),
    geo_type = "state",
    geo_values = "pa",
    issues = EpiRange("2020-05-09", "2020-05-15")
)
print(apicall10)

data10 = apicall10.df()
print(data10.head())
