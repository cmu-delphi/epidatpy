from datetime import date
from epidatpy import CovidcastEpidata, Epidata, EpiRange

apicall = Epidata.covidcast("fb-survey", "smoothed_cli", "day", "nation", EpiRange(20210405, 20210410), "us")

print(apicall)

classic = apicall.classic()
print(classic)

r = apicall.csv()
print(r[0:100])

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

for row in apicall.iter():
    print(row)

StagingEpidata = Epidata.with_base_url("https://staging.delphi.cmu.edu/epidata/")

epicall = StagingEpidata.covidcast(
    "fb-survey", "smoothed_cli", "day", "nation", EpiRange(date(2021, 4, 5), date(2021, 4, 10)), "*"
)
print(epicall._base_url)
