import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    from epidatpy import EpiDataContext, EpiRange

    ctx = EpiDataContext()
    df = ctx.epidata(
        source="nssp",
        signals="pct_ed_visits_influenza",
        geo_type="state",
        report_time_query=EpiRange("2025-01-01", "2025-10-16"),
    ).df()
    return (df,)


@app.cell
def _(df):
    df
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
