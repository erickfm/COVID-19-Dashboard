import streamlit as st
import os
import time
import plotly.express as px


import pandas as pd
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly
import plotly.graph_objects as go


def get_time_series(confirmed_cases_data, deaths_data):
    # Set days to predict
    test_days = 60
    forward_days = 30
    avg_window = 3

    # Load the data
    df = confirmed_cases_data

    # Filter the data for Los Angeles
    df_la = df[df['Admin2'] == 'New York']

    # Drop the non-date columns
    df_la = df_la.drop(columns=['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'])

    # Convert the data from wide to long format
    df_la_long = df_la.melt(var_name='Date', value_name='Cumulative Count')

    # Convert the 'Date' column to datetime format
    df_la_long['Date'] = pd.to_datetime(df_la_long['Date'])

    # Calculate the daily counts
    df_la_long['Daily Count'] = df_la_long['Cumulative Count'].diff()

    # If the first row is NaN due to the diff() operation, remove it
    df_la_long = df_la_long.dropna()

    la_data = df_la_long.copy()



    # Sort the data by date
    la_data = la_data.sort_values('Date')

    # Calculate the moving average
    la_data['moving_average'] = la_data['Daily Count'].rolling(window=avg_window).mean()




    # Rename the columns
    # Cumulative
    la_data.columns = ['ds', 'y', 'y_daily', 'y_avg']
    # Daily
    la_data.columns = ['ds', 'y_cum', 'y', 'y_avg']
    # Avg
    la_data.columns = ['ds', 'y_cum', 'y_daily', 'y']

    # Convert the 'ds' column to datetime format
    la_data['ds'] = pd.to_datetime(la_data['ds'])

    # Split the data into a training set and a test set
    train = la_data[:-test_days]
    test = la_data[-test_days:]

    # Define the model
    model = Prophet()

    # Fit the model to the training data
    model.fit(train)

    # Define a dataframe to hold the dates for which we want to make predictions
    future = model.make_future_dataframe(periods=test_days+forward_days)
    future['floor'] = 0

    # Use the model to make predictions
    forecast = model.predict(future)

    # Create the figure
    fig = plot_plotly(model, forecast)

    # # Add the forecast line
    # fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Forecast'))

    # Add the scatter plot for actual counts
    fig.add_trace(go.Scatter(x=test['ds'], y=test['y'], mode='markers', name='Actual ',
                  marker=dict(color='red', size=4)))

    # # Customize the layout
    # fig.update_layout(
    #     title='Forecast and Actual Counts for Los Angeles',
    #     xaxis_title='Date',
    #     yaxis_title='Counts',
    #     showlegend=True,
    #     legend=dict(x=0, y=1),
    #     width=800,
    #     height=500
    # )

    # Reorder the traces
    fig.data = tuple([fig.data[0],fig.data[4],fig.data[1],fig.data[2],fig.data[3]])

    return fig


def get_mapbox(confirmed_cases_data, deaths_data):
    # Take the most recent date from the datasets
    recent_date = confirmed_cases_data.columns[-1]

    # Calculate the fatality rate
    fatality_rate = deaths_data[recent_date] / confirmed_cases_data[recent_date] * 100

    # Prepare a DataFrame for plotting
    data = confirmed_cases_data[["Admin2", "Province_State", "Lat", "Long_"]].copy()
    data["Confirmed Cases"] = confirmed_cases_data[recent_date]
    data["Deaths"] = deaths_data[recent_date]
    data["Fatality Rate"] = fatality_rate
    data["County, State"] = data["Admin2"] + ', ' + data['Province_State']

    # Some Data Cleaning
    data = data[data["Confirmed Cases"] > 0]
    data = data[(data['Lat'] != 0) & (data['Long_'] != 0)]
    data = data[data['Deaths'] != 0]

    # Create a scatter_mapbox plot
    fig = px.scatter_mapbox(
        data,
        lat="Lat",
        lon="Long_",
        color="Fatality Rate",
        size="Deaths",
        hover_name="County, State",
        # hover_data=["Confirmed Cases", "Deaths"],
        zoom=3,
        title=f"COVID-19 Dashboard as of {recent_date}"
    )

    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig, data
