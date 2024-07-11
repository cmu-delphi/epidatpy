from datetime import date

from epidatpy import CovidcastEpidata, Epidata, EpiRange

print("Epidata Test")
apicall = Epidata.pub_covidcast("fb-survey", "smoothed_cli", "nation", "day", "us", EpiRange(20210405, 20210410))

# Call info
print(apicall)
# URL
print(apicall.request_url())

classic = apicall.classic()
print(classic)

data = apicall.json()
print(data[0])

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


StagingEpidata = Epidata.with_base_url("https://staging.delphi.cmu.edu/epidata/")

epicall = StagingEpidata.pub_covidcast(
    "fb-survey", "smoothed_cli", "nation", "day", "*", EpiRange(date(2021, 4, 5), date(2021, 4, 10))
)
print(epicall._base_url)


# Covidcast test
print("Covidcast Test")
epidata = CovidcastEpidata()
print(epidata.source_names)
epidata["fb-survey"].signal_df
apicall = epidata[("fb-survey", "smoothed_cli")].call(
    "nation",
    "us",
    EpiRange(20210405, 20210410),
)
print(apicall)

classic = apicall.classic()
print(classic)

data = apicall.json()
print(data[0])

df = apicall.df()
print(df.columns)
print(df.dtypes)
print(df.iloc[0])
df = apicall.df(disable_date_parsing=True)
print(df.columns)
print(df.dtypes)
print(df.iloc[0])
