# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "altair==6.0.0",
#     "marimo>=0.23.1",
#     "polars==1.39.3",
# ]
# ///

import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt

    return alt, mo, pl


@app.cell
def _():
    METRICS = {
        'VIS': 'Visits per year',
        'STD': 'Scaled by population',
        'HOT': 'Hot days',
        'OLD': 'Elderly dependency ratio',
    }

    YEAR_DICT = {str(year): year for year in range(1992, 2026)}

    BIG_HITTERS = ['DEU', 'NLD']
    WEST_EU     = ['AUT', 'BEL', 'CHE', 'FRA', 'GBR', 'IRL']
    NORDICS     = ['FIN', 'ISL', 'NOR', 'SWE']
    SOUTH_EU    = ['ESP', 'ITA', 'PRT']
    NOR_AMER    = ['CAN', 'USA']

    REGIONS = {
        'Big Hitters': BIG_HITTERS,
        'Western EU': WEST_EU,
        'Nordics': NORDICS,
        'Southern EU': SOUTH_EU,
        'North America': NOR_AMER,
    }

    COUNTRY_ISO_CODES = [
        'AUT',
        'BEL',
        'CAN',
        'CHE',
        'DEU',
        'ESP',
        'FIN',
        'FRA',
        'GBR',
        'IRL',
        'ISL',
        'ITA',
        'NLD',
        'NOR',
        'PRT',
        'SWE',
        'USA',
    ]
    return METRICS, REGIONS, YEAR_DICT


@app.cell
def _(mo):
    view_selector = mo.ui.dropdown(
        options=['Chart', 'Table'],
        value='Chart',
        label='View'
    )
    return (view_selector,)


@app.cell
def _(REGIONS, mo):
    region_selector = mo.ui.dropdown(
        options=['All'] + list(REGIONS.keys()),
        value='All',
        label='Region',
    )
    return (region_selector,)


@app.cell
def _(METRICS, mo):
    metric_selector = mo.ui.dropdown(
        options=[METRICS['VIS'], METRICS['STD'], METRICS['HOT'], METRICS['OLD']],
        value=METRICS['STD'],
        label='Metric',
    )
    return (metric_selector,)


@app.cell
def _(METRICS, metric_selector, mo):
    if metric_selector.value == METRICS['STD']:
        std_slider = mo.ui.slider(start=0, stop=40, step=1, value=20, label='Show if above X% of std below mean')
    # Need a default otherwise
    else:
        std_slider = mo.ui.slider(start=0, stop=10000, step=1, value=10000, label='Default')
    return (std_slider,)


@app.cell
def _(YEAR_DICT, mo):
    start_year_selector = mo.ui.dropdown(
        options=YEAR_DICT,
        value='1992',
        label='Start year',
        searchable=True,
    )
    return (start_year_selector,)


@app.cell
def _(YEAR_DICT, mo):
    end_year_selector = mo.ui.dropdown(
        options=dict(sorted(YEAR_DICT.items(), key=lambda item: item[0], reverse=True)),
        value='2025',
        label='End year',
        searchable=True,
    )
    return (end_year_selector,)


@app.cell
def _(METRICS, REGIONS, pl):
    def filtered_df(df, metric_selector, std_slider, region_selector, start_year_selector, end_year_selector):
        metric = metric_selector.value
        region = region_selector.value
        start_year = start_year_selector.value
        end_year = end_year_selector.value

        visits = pl.col('visits')
        year = pl.col('year').cast(pl.Int64)

        # Need to split this into two separate expressions
        # Otherwise Polars cannot figure it out
        start_year_expr = year >= start_year
        end_year_expr = year <= end_year

        df_year = df.filter(start_year_expr)

        if metric == METRICS['STD']:
            std_multiplier = std_slider.value / 100.0
            df_std = df_year.filter(visits >= (visits.mean() - (visits.std() * std_multiplier)))
        else:
            df_std = df_year

        # min_year = df_std.select(pl.min('year')).item()

        if region != 'All':
            df_region = df_std.filter(pl.col('iso_code').is_in(REGIONS[region]))
        else:
            df_region = df_std

        return df_region.filter(end_year_expr)

    return (filtered_df,)


@app.cell
def _(pl):
    def filtered_table(df):
        return df.select(pl.col('year', 'country', 'hot_days', 'visits', 'country_total', 'dep_percent', 'scaled'))

    return (filtered_table,)


@app.cell
def _(
    end_year_selector,
    filtered_df,
    metric_selector,
    pl,
    region_selector,
    start_year_selector,
    std_slider,
):
    df = (
        pl.read_csv('dashboard-df.csv', schema_overrides={'year': pl.String})
            .with_columns(
                scaled=(pl.col('visits') / pl.col('country_total') * 100).round(2)
            )
    )
    filtered = filtered_df(df, metric_selector, std_slider, region_selector, start_year_selector, end_year_selector)
    return (filtered,)


@app.cell
def _(METRICS, alt):
    def chart_config(df, metric_selector):
        if (metric_selector.value == METRICS['VIS']):
            y_axis = alt.Y('visits', title=METRICS['VIS'])
            chart_title = 'Overnight stays per year by country'
        elif (metric_selector.value == METRICS['STD']):
            y_axis = alt.Y('scaled', title='Overnight stays per total population (%)')
            chart_title = 'Overnight stays by population'
        elif (metric_selector.value == METRICS['HOT']):
            y_axis = alt.Y('hot_days', title=METRICS['HOT'])
            chart_title = 'Number of days by year'
        elif metric_selector.value == METRICS['OLD']:
            y_axis = alt.Y('dep_percent', title=METRICS['OLD'])
            chart_title = 'Ratio of retired to working age and youth'
        else:
            y_axis = alt.Y('scaled', title='Oops')
            chart_title = 'Oops'
        return y_axis, chart_title

    return (chart_config,)


@app.cell
def _(alt):
    def chart(df, y_axis, chart_title):
        return (
            alt.Chart(df)
            .mark_point(tooltip=True)
            .encode(
                x=alt.X('year', title='Year'),
                y=y_axis,
                color=alt.Color('country', title='Country'),
            )
            .properties(width=500, title=chart_title)
            .configure_scale(zero=True)
        )

    return (chart,)


@app.cell
def _():
    description = """
    This dashboard is part of the [tourists](https://github.com/amanda-amy-frost/tourists) data analysis mini-project. In chart view, you can select a country to the right of the chart to view tabular stats for that country. Click elsewhere on the chart to cancel your selection. See the ? tooltip to the bottom-right of the chart for more options.
    """
    return (description,)


@app.cell
def _(chart, chart_config, filtered, metric_selector, mo):
    alt_chart = chart(filtered, *chart_config(filtered, metric_selector))
    mo_chart = mo.ui.altair_chart(alt_chart, legend_selection=['country', 'year'])
    return (mo_chart,)


@app.cell
def _(
    description,
    end_year_selector,
    filtered,
    filtered_table,
    metric_selector,
    mo,
    mo_chart,
    region_selector,
    start_year_selector,
    std_slider,
    view_selector,
):
    filter_options = [
        mo.md(description),
        mo.md('&nbsp;'),
        mo.md('# Filters'),
        mo.md('&nbsp;'),
        view_selector,
        mo.md('&nbsp;'),
        region_selector,
        mo.md('&nbsp;'),
        metric_selector,
    ]

    if std_slider.value != 10000:
        filter_options.extend([
            # mo.md('&nbsp;'),
            # min_year,
            mo.md('&nbsp;'),
            std_slider,
        ])

    filter_options.extend([
        mo.md('&nbsp;'),
        start_year_selector,
        mo.md('&nbsp;'),
        end_year_selector,
    ])

    filter_panel = mo.vstack(filter_options)

    chart_view = mo.vstack([
        mo_chart,
        mo_chart.value.select('country', 'year', 'scaled', 'visits', 'hot_days', 'dep_percent'),
    ])

    table_view = filtered_table(filtered)

    mo.vstack([
        mo.md('#Tourism Dashboard'),
        mo.md('&nbsp;'),

        mo.hstack([
            filter_panel,
            mo.md('   '),  # Horizontal spacing
            chart_view if view_selector.value == 'Chart' else table_view
        ])
    ])
    return


if __name__ == "__main__":
    app.run()
