from epidatpy import EpiDataContext, EpiRange
from epidatpy._endpoints import AEpiDataEndpoints
import inspect
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
    geo_type = "state",
    geo_values = "pa,ca,fl",
    time_type = "day",
    time_values = EpiRange(20210405, 20210410))

data = apicall.df()

fig, ax = plt.subplots(figsize=(6, 5))
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)

data.pivot_table(values = "value", index = "time_value", columns = "geo_value").plot(
    xlabel="Date",
    ylabel="CLI",
    ax = ax,
    linewidth = 1.5
)

plt.title("Smoothed CLI from Facebook Survey", fontsize=16)
plt.subplots_adjust(bottom=.2)
plt.savefig("docs/images/Getting_Started.png", dpi=300)

results = []
for as_of_date in ["2020-05-07", "2020-05-14", "2020-05-21", "2020-05-28"]:
    apicall = epidata.pub_covidcast(
        data_source = "doctor-visits",
        signals = "smoothed_adj_cli",
        time_type = "day",
        time_values = EpiRange("2020-04-20", "2020-04-27"),
        geo_type = "state",
        geo_values = "pa",
        as_of = as_of_date)

    results.append(apicall.df())

final_df = pd.concat(results)
final_df["issue"] = final_df["issue"].dt.date

fig, ax = plt.subplots(figsize=(6, 5))
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["top"].set_visible(False)

def sub_cmap(cmap, vmin, vmax):
    return lambda v: cmap(vmin + (vmax - vmin) * v)

final_df.pivot_table(values = "value", index = "time_value", columns = "issue").plot(
    xlabel="Date",
    ylabel="CLI",
    ax = ax,
    linewidth = 1.5,
    colormap=sub_cmap(plt.get_cmap('viridis').reversed(), 0.2, 1)
)

plt.title("Smoothed CLI from Doctor Visits", fontsize=16)
plt.subplots_adjust(bottom=.2)
plt.savefig("docs/images/Versioned_Data.png", dpi=300)

# Get AEpiDataEndpoints methods that start with pvt_ and pub_
endpoints = [x for x in inspect.getmembers(AEpiDataEndpoints) if x[0].startswith("pvt_") or x[0].startswith("pub_")]

# 
data = {e[0]: e[1].__doc__.split("\n")[0] if e[1].__doc__ else "" for e in endpoints}

table = pd.DataFrame(data.items(), columns = ["Endpoint", "Description"])

table.to_csv("docs/data/endpoints.csv", index = False)
