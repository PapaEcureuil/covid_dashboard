import pandas as pd
import streamlit as st
from datetime import date, timedelta
from plotly import graph_objs as go
import pydeck
from resources import utils

@st.cache
def get_global_data(last_date=date.today() - timedelta(1), ts_type='Confirmed'):
    """Get full time series aggregated by Country

    Parameters
    ----------
    last_date : date, optional
        [description], by default date.today()-timedelta(1)
    """
    global_ts_link = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{ts_type.lower()}_global.csv'
    return pd.read_csv(global_ts_link).groupby('Country/Region').sum().drop(['Lat', 'Long'], axis=1)\
        .T.set_index(pd.date_range(start='2020-01-22', end=last_date))

@st.cache
def get_locations(ts_type):
    global_ts_link = f'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{ts_type.lower()}_global.csv'
    return pd.read_csv(global_ts_link).groupby('Country/Region').mean().loc[:, ['Lat', 'Long']]

@st.cache
def get_detailed_daily_reports(last_date=date.today() - timedelta(1), ts_type='Confirmed'):
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
            daily_df[province_col] = daily_df[province_col].astype(str).\
                apply(lambda x: x.split(',')[-1].replace(' ', '').replace('.', '')).replace(a2_to_fullname)

        daily_df = daily_df.groupby(province_col).sum()[[ts_type]]


        df = df.assign(**{x:None for x in daily_df.index if x not in df.columns})
        df.loc[day, daily_df.index] = daily_df[ts_type].values
    return df[[x for x in a2_to_fullname.values() if x in df.columns]].fillna(0)


def plot_df(df,  highlighted_cols, plot_title=''):
    # Dropdown menu to choose between linear and log scale
    visibility = lambda x: True if x in highlighted_cols else 'legendonly'

    updatemenus = list([
        dict(active=1,
         buttons=list([
            dict(label='Log Scale',
                 method='update',
                 args=[{'visible': [visibility(x) for x in df.columns]},
                       {'title': 'Log scale',
                        'yaxis': {'type': 'log', 'range': [0, 5], 'fixedrange': False}}]),
            dict(label='Linear Scale',
                 method='update',
                 args=[{'visible': [visibility(x) for x in df.columns]},
                       {'title': 'Linear scale',
                        'yaxis': {'type': 'linear', 'fixedrange': False}}])
            ]),
        )
    ])


    fig = go.Figure(layout=dict(title=plot_title, width=1500, height=700, updatemenus=updatemenus))

    for col in df.columns:
        fig.add_scatter(x=df.index, y=df[col], name=col, visible=visibility(col))

    fig.update_layout(
        xaxis=dict(
            rangeslider=dict(
            visible=True
        )),
        yaxis = dict(
            fixedrange = False
        ))
    return fig

def _max_width_(nb_pixels=1500):
    max_width_str = f"max-width: {nb_pixels}px;"
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


@st.cache(persist=True)
def get_world_as_polygons():
    """Can't get GeoJson Layers to work on pydeck, nor multipolygon, so we'll hack it with
    Polygons and redondant countries
    """
    raw = pd.read_json('resources/countries.geojson')
    df = pd.DataFrame()

    df['coords'] = raw.features.apply(lambda x: x['geometry']['coordinates'])
    df['country'] = raw.features.apply(lambda x: x['properties']['ADMIN'])
    df['len_poly'] = df.coords.apply(lambda x: len(x))

    simple = df.query('len_poly==1')
    complicated = df.query('len_poly>1')
    complicated = complicated.explode('coords')

    return simple.append(complicated)[['coords', 'country']]

def _hide_menu_():
    hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        </style>
    """
    st.markdown(hide_menu_style, unsafe_allow_html=True)

def main():
    _max_width_()
    _hide_menu_()
    st.title('Stay the fuck Home :derelict_house_building:')
    ts_type = st.sidebar.selectbox('Confirmed Cases / Deaths', ['Confirmed', 'Deaths'])

    show_graph = st.checkbox('Show Graph ?', False)
    if show_graph:
        df_type = st.sidebar.selectbox('World Global or US States', ['Global', 'US States'])
        df = get_global_data(ts_type=ts_type) if df_type=='Global' else get_detailed_daily_reports(ts_type=ts_type)
        default_countries = ['France', 'Italy', 'Spain', 'US'] if df_type == 'Global' else list(df.columns.values)
        highlighted_cols = st.multiselect('Select multiple countries, others will be hidden on chart.', list(df.columns.values), default_countries)

        st.plotly_chart(plot_df(df, highlighted_cols, plot_title=df_type,))

    show_map = st.checkbox('Show Map?', True)
    if show_map:
        d = st.date_input('Choose date', date.today() - timedelta(1))

        df_to_join = get_global_data(ts_type=ts_type).loc[d]
        polygons = get_world_as_polygons()
        df_to_join = df_to_join.rename(index=utils.COUNTRIES_NAME)
        display = polygons.join(df_to_join, on='country').dropna()
        display.columns = ['coords', 'country', 'cases']
        display['color'] = pd.cut(display.cases,
            bins=len(utils.COLOR_RANGE),
            labels=[str(x) for x in utils.COLOR_RANGE],
            include_lowest=True)

        geojson = pydeck.Layer(
            'PolygonLayer',
            display,
            opacity=1,
            get_polygon='coords',
            stroked=True,
            filled=True,
            extruded=True,
            # wireframe=True,
            get_elevation='cases * 10',
            elevation_range=[0, 100000],
            get_fill_color='color',
            get_line_color='color',
            pickable=True
        )

        INITIAL_VIEW_STATE = pydeck.ViewState(
            latitude=0,
            longitude=0,
            zoom=1,
            max_zoom=8,
            pitch=25,
            bearing=0
        )

        st.pydeck_chart(pydeck.Deck(
            layers=[geojson],
            initial_view_state=INITIAL_VIEW_STATE))


    st.info('_Covid Data fetched from https://github.com/CSSEGISandData/COVID-19_')
    st.info('_Countries geojson downloaded at https://datahub.io/core/geo-countries_')
    st.info('_Code available at https://github.com/PapaEcureuil/covid_dashboard_')

if __name__ == "__main__":
    main()