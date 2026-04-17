import marimo

__generated_with = "0.23.1"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt

    return alt, mo, pl


@app.cell
def _(mo):
    metric_selector = mo.ui.dropdown(
        options=['std'],
        value='std',
        label='Select metric'
    )
    return (metric_selector,)


@app.cell
def _(mo):
    view_selector = mo.ui.dropdown(
        options=['chart', 'table'],
        value='chart',
        label='Select view'
    )
    return (view_selector,)


@app.cell
def _(metric_selector, mo):
    if metric_selector.value == 'std':
        metric_slider = mo.ui.slider(0, 1.5, value=0.3, step=0.05, label='Show if above selected std below mean')
    else:
        metric_slider = mo.ui.slider(0, 100, value=1, step=1, label='Default')
    return (metric_slider,)


@app.cell
def _(pl):
    def filtered_df(df, metric_selector, metric_slider):
        metric = metric_selector.value
        slider_val = metric_slider.value

        if metric == 'std':
            # slider_val = number of standard deviations
            std = df.select(pl.col('scaled').std()).item()
            mean = df.select(pl.col('scaled').mean()).item()
            lower = mean - (slider_val * std)
            return df.filter(pl.col('scaled') >= lower)

    return (filtered_df,)


@app.cell
def _(filtered_df, metric_selector, metric_slider, pl):
    df = (
        pl.read_csv('dashboard-df.csv', schema_overrides={'year': pl.String})
            .with_columns(
                scaled=pl.col('visits') / pl.col('country_total') * 100
            )
    )
    filtered = filtered_df(df, metric_selector, metric_slider)
    return (filtered,)


@app.cell
def _(alt, pl):
    def chart(df):
        df_plot = df.with_columns(
            (pl.col('visits') / pl.col('country_total') * 100).alias('scaled')
        )

        return (
            alt.Chart(df_plot)
            .mark_point(tooltip=True)
            .encode(
                x=alt.X('year', title='Year'),
                y=alt.Y('scaled', title='Overnight stays per total population (%)'),
                color=alt.Color('country', title='Country'),
            )
            .properties(width=500, title='Overnight stays by population')
            .configure_scale(zero=True)
        )

    return (chart,)


@app.cell
def _():
    description = """
    This dashboard is part of the [tourists](https://github.com/amanda-amy-frost/tourists) data analysis mini-project. Click on the link for more details.
    """
    return (description,)


@app.cell
def _(
    chart,
    description,
    filtered,
    metric_selector,
    metric_slider,
    mo,
    view_selector,
):
    filter_panel = mo.vstack([
        mo.md(description),
        mo.md('&nbsp;'),
        mo.md('# Filters'),
        mo.md('&nbsp;'),
        view_selector,
        mo.md('&nbsp;'),
        metric_selector,
        mo.md('&nbsp;'),
        metric_slider,
    ])

    mo.vstack([
        mo.md('#Tourism Dashboard'),
        mo.md('&nbsp;'),

        mo.hstack([
            filter_panel,
            mo.md('   '),  # horizontal spacing
            chart(filtered) if view_selector.value == 'chart' else filtered
        ])
    ])
    return


if __name__ == "__main__":
    app.run()
