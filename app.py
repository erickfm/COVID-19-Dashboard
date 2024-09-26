import streamlit as st
import pandas as pd
from dashboard.constants import github_image_path
from streamlit_plotly_events import plotly_events

from dashboard.functions import get_mapbox, get_time_series, get_3D_scatter
from dashboard.constants import margins_css

st.set_page_config(page_title='COVID-19 Dashboard', page_icon="🌎", layout="wide", initial_sidebar_state='collapsed')
st.markdown(margins_css, unsafe_allow_html=True)

with st.sidebar:
    main_page = st.button('COVID-19 Dashboard', use_container_width=1)
    about_page = st.button('About', use_container_width=1)
    if not about_page:
        main_page = True

if main_page:
    # Load data
    confirmed_cases_data = pd.read_csv(
        'https://raw.githubusercontent.com/erickfm/COVID/main/data/time_series_covid19_confirmed_US.csv')
    deaths_data = pd.read_csv(
        'https://raw.githubusercontent.com/erickfm/COVID/main/data/time_series_covid19_deaths_US.csv')
    demographics_data = pd.read_csv('https://raw.githubusercontent.com/erickfm/COVID/main/data/county_demographics.csv')

    st.write('## COVID-19 Dashboard')
    col_1, col_2 = st.columns([16, 10])
    col_1a, col_1b = col_1.columns([1, 1])

    col_2top = col_2.container()
    col_2a, col_2b, col_2c, col_2d = col_2.columns([15, 15, 10, 8])
    col_2bottom = col_2.container()
    size = col_1a.selectbox('size', ['Fatality Rate', 'Deaths', 'Confirmed Cases', 'Daily Fatality Rate'], index=1)
    color = col_1b.selectbox('color', ['Fatality Rate', 'Deaths', 'Confirmed Cases', 'Daily Fatality Rate'], index=0)
    dataset = col_2c.selectbox('Dataset', ['Deaths', 'Cases'], index=1)
    agg_option = col_2b.selectbox('Aggregation', ['Cumulative', 'Daily', 'Daily Rolling Average'])
    col_2d.write('#')

    predictive_analytics = col_2d.checkbox('Forecast')
    if predictive_analytics:
        forward_days = col_2bottom.slider('Forecast Length', 0, 1095, 0)
        test_days = col_2bottom.slider('Test Length', 0, 1095, 0)
    else:
        forward_days = None
        test_days = None

    if agg_option == 'Daily Rolling Average':
        avg_window = col_2bottom.slider('Average Window', 2, 30, value=7)
    else:
        avg_window = None

    fig, data = get_mapbox(confirmed_cases_data, deaths_data, demographics_data, size, color)

    table = data.drop(columns=['Lat', 'Long_', 'County, State', 'Daily Fatality Rate', 'Daily Deaths'])
    table = table.drop(columns=['County', 'State']).rename(
        columns={'Admin2': 'County', 'Province_State': 'State', 'Confirmed Cases': 'Cases'})
    with col_1:
        selected_points_map = plotly_events(fig, )  # use_container_width=True, theme=None)
        if selected_points_map:
            row_index = selected_points_map[0]["pointIndex"]
            table = table[row_index:row_index + 1]
    col_1_alpha, col_1_beta, dummy_col = col_1.columns([10, 10, 2])
    col_1_alpha.info(f'### Average Fatality Rate: {round(data["Fatality Rate"].mean(), 3)}')
    col_1_beta.info(f'### Median Fatality Rate: {round(data["Fatality Rate"].median(), 3)}')

    col_2top.write('##### US Counties')
    if predictive_analytics:
        if avg_window:
            table_height = 50
        else:
            table_height = 100
    else:
        if avg_window:
            table_height = 285
        else:
            table_height = 400

    fig_scatter = get_3D_scatter(data)
    st.write('### Fatality Rate Correlations')
    selected_points_scatter = plotly_events(fig_scatter)
    if selected_points_scatter:
        row_index = selected_points_scatter[0]["pointNumber"]
    if selected_points_map or selected_points_scatter:
        if selected_points_map:
            row_index = selected_points_map[0]["pointIndex"]
        else:
            row_index = selected_points_scatter[0]["pointNumber"]
            c = data[row_index:row_index + 1]['County'].iloc[0].strip()
            s = data[row_index:row_index + 1]['State'].iloc[0].strip()
            table = table[(table['County'].str.contains(c)) & (table['State'].str.contains(s))]
        county_state = col_2a.selectbox('County',
                                        table['County'] + ', ' + table['State'])
    else:
        county_state = col_2a.selectbox('County',
                                        confirmed_cases_data['Admin2'] + ', ' + confirmed_cases_data['Province_State'],
                                        index=234)
    fig_ts = get_time_series(confirmed_cases_data,
                             deaths_data,
                             dataset,
                             county_state,
                             test_days,
                             forward_days,
                             agg_option,
                             avg_window,
                             predictive_analytics)
    col_2bottom.plotly_chart(fig_ts, use_container_width=True, theme=None)
    col_2top.dataframe(table, use_container_width=True, hide_index=True, height=table_height)
    # st.write('#')
    # with st.expander(''):
    #     selected_points_scatter_null = plotly_events(fig_scatter, key='null')



if about_page:
    st.markdown('# About \n')
    st.write(
        "Plotly-based Streamlit dashboard using CSSE COVID-19 data and Census data aggregated by the CORGIS Dataset Project\n\n"
        "Inspiration from [CSSE COVID-19 Dashboard](https://www.arcgis.com/apps/dashboards/bda7594740fd40299423467b48e9ecf6)\n\n"
        "Built by [Erick Martinez](https://github.com/erickfm)."
        "")
    st.markdown(
        f"""<div><a href="https://github.com/erickfm/COVID"><img src="{github_image_path}" style="padding-right: 10px;" width="6%" height="6%"></a>""",
        unsafe_allow_html=1)
