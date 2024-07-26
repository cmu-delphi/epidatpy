from datetime import date

from epidatpy import CovidcastEpidata, EpiDataContext, EpiRange

print("Epidata Test")
epidata = EpiDataContext(use_cache=True, cache_max_age_days=1)
apicall = epidata.pub_covidcast("fb-survey", "smoothed_cli", "nation", "day", "us", EpiRange(20210405, 20210410))

# Call info
print(apicall)
# URL
print(apicall.request_url())

classic = apicall.classic()
print(classic)

df = apicall.df()
print(df.columns)
print(df.dtypes)
print(df.iloc[0])
print(df)
# Classic
classic = apicall.classic()
# DataFrame
df = apicall.df(disable_date_parsing=True)
print(df.columns)
print(df.dtypes)
print(df.iloc[0])


staging_epidata = epidata.with_base_url("https://staging.delphi.cmu.edu/epidata/")

epicall = staging_epidata.pub_covidcast(
    "fb-survey", "smoothed_cli", "nation", "day", "*", EpiRange(date(2021, 4, 5), date(2021, 4, 10))
)
print(epicall._base_url)


# Covidcast test
print("Covidcast Test")
epidata = CovidcastEpidata(use_cache=True, cache_max_age_days=1)
print(epidata.source_names())
print(epidata.signal_names("fb-survey"))
epidata["fb-survey"].signal_df
apicall = epidata[("fb-survey", "smoothed_cli")].call(
    "nation",
    "us",
    EpiRange(20210405, 20210410),
)
print(apicall)

classic = apicall.classic()
print(classic)

df = apicall.df()
print(df.columns)
print(df.dtypes)
print(df.iloc[0])
df = apicall.df(disable_date_parsing=True)
print(df.columns)
print(df.dtypes)
print(df.iloc[0])
