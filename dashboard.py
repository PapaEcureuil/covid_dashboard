import pandas as pd
import streamlit as st
from datetime import date, timedelta
from plotly import graph_objs as go

@st.cache
def get_global_data(last_date=date.today() - timedelta(1)):
    """Get full time series aggregated by Country

    Parameters
    ----------
    last_date : date, optional
        [description], by default date.today()-timedelta(1)
    """
    global_ts_link = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    return pd.read_csv(global_ts_link).groupby('Country/Region').sum().drop(['Lat', 'Long'], axis=1).T.set_index(pd.date_range(start='2020-01-22', end=last_date))

@st.cache
def get_detailed_daily_reports(last_date=date.today() - timedelta(1)):
    """Get daily reports, detailed by province/region, which is in form "one csv per day"
    We need this for US states as they are not detailed in the "global" report.

    Parameters
    ----------
    last_date : [type], optional
        [description], by default date.today()-timedelta(1)
    """
    print(last_date)
    df = pd.DataFrame(index=pd.date_range(start='2020-01-22', end=last_date))
    states = pd.read_pickle('resources/states.pkl')
    a2_to_fullname = {x['abbr']: x['name'] for x in states}


    for day in pd.date_range(start='2020-01-22', end=last_date):
        daily_link = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/{day.strftime("%m-%d-%Y")}.csv'
        daily_df = pd.read_csv(daily_link)
        country_col = next((x for x in daily_df.columns if 'Country' in x), None)
        daily_df = daily_df.loc[daily_df[country_col] == 'US']
        # CSV columns have changed over time
        province_col = next((x for x in daily_df.columns if 'Province' in x), None)
        # From 01-22 to 01-31, full state name
        # Then till 03-09: county, A2 state
        # Then from 03-10, full state name
        if day < pd.to_datetime('2020-03-10') and day > pd.to_datetime('2020-01-31'):
            # Get only A2 state name and translate it to its full name
            daily_df[province_col] = daily_df[province_col].astype(str).apply(lambda x: x.split(',')[-1].replace(' ', '').replace('.', '')).replace(a2_to_fullname)

        daily_df = daily_df.groupby(province_col).sum()[['Confirmed']]


        df = df.assign(**{x:None for x in daily_df.index if x not in df.columns})
        df.loc[day, daily_df.index] = daily_df.Confirmed.values
    return df[[x for x in a2_to_fullname.values() if x in df.columns]].fillna(0)

def plot_df(df, plot_title=''):
    # Dropdown menu to choose between linear and log scale
    updatemenus = list([
    dict(active=1,
         buttons=list([
            dict(label='Log Scale',
                 method='update',
                 args=[{'visible': [True, True]},
                       {'title': 'Log scale',
                        'yaxis': {'type': 'log'}}]),
            dict(label='Linear Scale',
                 method='update',
                 args=[{'visible': [True, False]},
                       {'title': 'Linear scale',
                        'yaxis': {'type': 'linear'}}])
            ]),
        )
    ])


    fig = go.Figure(layout=dict(title=plot_title, width=1500, height=700, updatemenus=updatemenus))

    for col in df.columns:
        fig.add_scatter(x=df.index, y=df[col], name=col)
    return fig


def _max_width_():
    max_width_str = f"max-width: 1500px;"
    st.markdown(
        f"""
    <style>
    .reportview-container .main .block-container{{
        {max_width_str}
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

def main():
    _max_width_()
    st.title('Stay the fuck Home')
    df_type = st.selectbox('World Global or US States', ['Global', 'States'])
    df = get_global_data() if df_type=='Global' else get_detailed_daily_reports()

    st.plotly_chart(plot_df(df, plot_title=df_type))


if __name__ == "__main__":
    main()