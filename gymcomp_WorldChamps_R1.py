#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 13:38:51 2024

@author: joelgagnon
"""

#%% gymcomp R3

#2024-10-01
# upgrading for olympic data
# will now have Neutral Deductions/Penalty to account for
# there's now a need for two vault options for a single competition day

# 3 tabs with 3 key features
# 1: Competition Overview
# 2: Individual Athlete Analysis
# 3: Team Scenarios

#%% HARDCODED STUFF

SERIES = "WorldChamps2025"

#%% Imports

import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import math
import plotly.graph_objs as go
import plotly.express as px
import pickle
import os
import itertools
from plotly.subplots import make_subplots
#dash authentication
# import dash_auth # pip install dash-auth==2.0.0. <- add this to requirements.txt

# Import the print function
from builtins import print

#import the team scenarios calc
from team_scenario_calcs_R1 import team_score_calcs

#ordered dict
from collections import OrderedDict

#date time to sort competitions
from datetime import datetime

#time for debugging some progress bar stuff
import time

#garbage collection (might need to update requirements.txt)
# import gc
#%% Import Data 
#use absolute path

# Get the absolute path to the directory containing the main app file
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the file
#file path and csv file name
path = "production_data/WorldChamps2025"
# pkl_file = "CottbusEF_mag_athletes"
pkl_file = "WorldChamps2025_athletes_R1"

file_path = os.path.join(base_dir, path+"/"+pkl_file)

#note I had some numpy errors
#the fix was to upgrade numpy
#then RECREATE PICKLE FILE using that version of numpy
#then run script again


with open(file_path, 'rb') as f:
    database = pickle.load(f)

# print("Database loaded successfully.")

#%%  Function to calculate the color based on the score
# def get_color(score, max_score):
#     if math.isnan(score):
#         return 'black'  # or any other default color
#     else:
#         # Calculate the color based on the score and max score
#         color_value = score / max_score
#         return color_value

#%% Setup App, Title, Authentication
app = dash.Dash(__name__, suppress_callback_exceptions=True) #, external_stylesheets=[dbc.themes.MORPH])
# app = dash.Dash(__name__,suppress_callback_exceptions=True, external_stylesheets=[dbc.themes.MORPH])

app.title = "STOI Demo"

# # Keep this out of source code repository - save in a file or a database
# VALID_USERNAME_PASSWORD_PAIRS = {
#     'hello3': 'world'
# }

# #ssecret key for flask
# app.secret_key = 'mensartisticgymnasticsdemo'  # Set your secret key here

# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )

########################
#%% Global Variables ###
########################

#I want to make the drop down selectors take up less width
dropdown_style = {'width': '50%'}  # Adjust the width as needed
dropdown_style1 = {'width': '100%'}  # Adjust the width as needed
dropdown_style2 = {'width': '80%'}  # Adjust the width as needed
tlas = ['FX', 'PH', 'SR', 'VT1','VT2', 'PB', 'HB'] #remove AA for World cups, 'AA']
# tlas = ['FX', 'PH', 'SR', 'VT1', 'PB', 'HB'] 
exclude_keys = ["overview", "competition_acronyms", "category_acronyms","series_acronyms","competition_dates","series_dates"]
tla_dict = {
            "FX":"Floor Exercise",
            "PH":"Pommel Horse",
            "SR":"Still Rings",
            "VT1":"Vault 1",
            "VT2":"Vault 2",
            "PB":"Parallel Bars",
            "HB":"Horizontal Bar",
            # "AA":"All Around",
                }

#%% Helpful functions

def get_category_data_for_competition_day(database, competition, categories, results, apparatus):
    #Since we made category a multi-select, we need to update how the code works
    #categories is now a list
    
    data = {}
    
    for athlete, competitions in database.items():
        
        if athlete not in exclude_keys:
            # print(f"athlete: {athlete}")
            # print(f"competition: {competition}")
            # print(f"competitions: {competitions.keys()}")
            if competition in competitions.keys():
                # print(f"athlete: {athlete}")
                #loop through categories if they are selected
                if categories:
                    for category in categories:
                        if category == database[athlete][competition]['category']:
                            #need to make sure we have selected results, it might be none
                            if results != None:
                                try:
                                    data[athlete] = database[athlete][competition][results][apparatus]
                                    #I also want to add the category of the athlete into the data
                                    #this is because we have multi-select categories now and it is now useful to know
                                    data[athlete]['category'] = database[athlete][competition]['category']
                                    #need to add country code now too
                                    data[athlete]['country'] = database[athlete][competition]['country']
                                    
                                except:
                                    #There are some scenarios where an athlete only competes day 1 but not day 2 or vice versa
                                    #also important for finals
                                    #in those cases, if we cant find the data,do not try to set it as it does not exist
                            
                                    # print(f"couldn't save {athlete} data for {results}")
                                    pass
                                    
    # print(data)
    return data

###################################
#%% Tab 1: Competition Overview ###
###################################
# Function to calculate the color based on the score
def get_color(score, min_score, max_score):
    print(f"score: {score}")
    print(f"min_score: {min_score}")
    print(f"max_score: {max_score}")
    if math.isnan(score):
        return 'black'  # or any other default color
    else:
        # Calculate the color based on the score and max score
        color_value = score / (max_score - min_score)
        return color_value

def update_histogram(database, competition, categories, results, apparatus, xaxis_var='Score'):
    bubble_data = get_category_data_for_competition_day(database, competition, categories, results, apparatus)
    if not bubble_data:
        # return px.histogram()  # empty figure
        return go.Figure() # empty figure

    # Extract valid scores
    # scores = [stats['Score'] for stats in bubble_data.values() if not np.isnan(stats['Score']) and stats['Score'] > 0]

    # Extract valid values for the chosen x-axis
    values = []
    for stats in bubble_data.values():
        val = stats.get(xaxis_var)
        if val is not None and not np.isnan(val) and stats.get("D")!=0: #if a score is zero, I dont want it on the list I get
            values.append(val)
    
    #check if we have values
    #sometimes we have no entries (ex. no stick bonus on PH, or no sticks in a dataset, or no ND in dataset)
    if not values:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for this selection",
            xref="paper", yref="paper",
            x=0.5, y=0.5,  # center of the chart
            showarrow=False,
            font=dict(size=16, color="gray"),
            align="center",
        )
        # Optional layout tweaks so it still looks like a chart area
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            template="plotly_white",
        )
        # return go.Figure() # empty figure
        return fig
    
    
    fig = px.histogram(
        # x=scores,
        x=values,
        nbins=20,
        # labels={'x': 'Score'},
        labels={'x': xaxis_var},
        title=f"{xaxis_var} Distribution ({apparatus})",
        color_discrete_sequence=['#636efa'],
        # text_auto='.3f'
    )

    # Add outlines around each bar
    fig.update_traces(
        marker_line_color='white',   # or 'black' for sharper contrast
        marker_line_width=1.0,
        # hovertemplate=(
        #     "<b>Bin range:</b> %{x.start:.3f} – %{x.end:.3f}<br>"
        #     "<b>Count:</b> %{y}<extra></extra>"
        # )
    )

    fig.update_layout(
        # xaxis_title='Score',
        xaxis_title=xaxis_var,
        yaxis_title='Frequency',
        template='plotly_white',
        bargap=0.0 #0.1
    )
    
        
    # Optional: specify bin size manually (e.g., every 0.5 points)
    val_min = np.floor(np.min(values) * 10) / 10 - 0.1
    val_max = np.ceil(np.max(values) * 10) / 10 + 0.1
    val_range = val_max - val_min
    if val_range < 1.0:
        # Expand symmetrically around the data, but not below 0
        mid = np.round(np.mean(values),1)#round to 1 decimal
        val_min = mid-0.5
        val_max = val_min + 1.0

    fig.update_traces(xbins=dict(start=val_min, end=val_max, size=0.1))
    # Explicitly set axis range so Plotly doesn’t autozoom
    fig.update_xaxes(range=[val_min, val_max])
    
    
    #do some statistical calcs
    # Compute mean and std for the distribution
    mean = np.mean(values)
    std = np.std(values)
    median = np.median(values)
    min_val = np.min(values)
    max_val = np.max(values)
    
    
    stats_text = f"Min: {min_val:.3f}<br>Max: {max_val:.3f}<br>Mean: {mean:.3f}<br>Median: {median:.3f}<br>Std Dev: {std:.3f}"
    
    fig.add_annotation(
        text=stats_text,
        xref="paper", yref="paper",
        x=1.05, y=0.95,
        showarrow=False,
        align="right",
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="gray",
        borderwidth=1,
        font=dict(size=12)
    )
    
    
    
    return fig

# Function to update the bubble plot
def update_bubble_plot(database, competition, categories, results, apparatus):
    data = {'x': [], 'y': [], 'category': [], 'size': [], 'name': [], 'score': [], 'ND':[], 'Bonus':[],  'color': []}
    
    #filter the data 

    bubble_data = get_category_data_for_competition_day(database, competition, categories, results, apparatus)
    
    if not bubble_data:
        # print("no bubble plot data")
        # table = html.Table()
        pass
    else:
        # print("we have bubble data!")
        # print(bubble_data)
        
        #TODO change this max score thing likely
        max_score = np.nanmax([values['Score'] for values in bubble_data.values()])
        min_score = np.nanmin([values['Score'] for values in bubble_data.values()])
        # max_score = 16
        # print(f"max score: {max_score}")
        exp = 3  # Adjust this as needed
        
        for name, stats in bubble_data.items():
            
            if np.isnan(stats['E']) or stats['E']==0.0:
                pass
            else:
                # print(f"name: {name}")
                # print(f"stats: {stats}")
                #I've already filtered the apparatus
                if stats['E'] == 0.0:
                    data['x'].append(np.nan)
                else:
                    data['x'].append(stats['E'])
    
                if stats['D'] == 0.0:
                    data['y'].append(np.nan)
                else:
                    data['y'].append(stats['D'])
    
                data['name'].append(name)
                data['score'].append(stats['Score'])
                data['ND'].append(stats['ND'])
                data['Bonus'].append(stats['Bonus'])
                
                # Make it zero if it's nan
                if math.isnan(stats['Score']):
                    size = 0.0
                    color = 0.0
                else:
                    size = stats['Score']
                    color = stats['Score']
                    
                data['color'].append(get_color(color ** exp, min_score, max_score ** exp))
                    
                size_exp = 1.5
                if apparatus == "AA":
                    data['size'].append((size / 6) ** size_exp)
                else:
                    data['size'].append(size ** size_exp)
                    
                #add category data
                data['category'].append(stats['category'])
        print(data)
    return data

#OLD CODE BEFORE TABLE WAS FILTERABLE
def update_table(database, competition, categories, results, apparatus, selected_athlete=None):
    # Filter the database based on selected day and apparatus
    # filtered_data = {name: stats for name, values in database.items() if day in values for app, stats in values[day].items() if app == apparatus}
    
    table_data = get_category_data_for_competition_day(database, competition, categories, results, apparatus)
    
    # Ensure that the table_data dictionary is not empty
    if not table_data:
        # print("no table data")
        table = html.Table()
    else:
        # print("we have table data!")
        # Flatten the dictionary and convert to DataFrame
        df = pd.DataFrame.from_dict(table_data, orient='index')
        
        # Check if the DataFrame has the expected columns
        expected_columns = ['Score', 'E']  # Add other expected columns here
        if not set(expected_columns).issubset(df.columns):
            return None
        
        # Sort DataFrame by Score in descending order (if tie, sort by E score for now)
        df = df.sort_values(by=['Score', 'E'], ascending=[False, False])
        
        # Keep only rows with a valid D  score (not NaN or zero)
        # sometimes a legitimate score can be zero so best to check
        # df = df[(df['D'].notna() & (df['D'] != 0)) | (df['E'].notna() & (df['E'] != 0))]
        df = df[(df['D'].notna() & (df['D'] != 0))]
        
        # print(f"df: {df}")
        # Reset index to include Athlete name as a column
        df = df.reset_index().rename(columns={'index': 'Athlete name'})
        
        #Fill any nans to 0.000
        df = df.fillna(0.000)
        
        # Truncate score values to 3 decimal points (do not round)
        df['D score'] = df['D'].map('{:.3f}'.format)
        df['E score'] = df['E'].map('{:.3f}'.format)
        df['Score'] = df['Score'].map('{:.3f}'.format)
        
        # print(results)
        if results == "average":
            #due to averaging, nice to add another decimal point
            df['ND'] = df['ND'].map('{:.2f}'.format) #2 decimal point for neutral deductions
            df['Bonus'] = df['Bonus'].map('{:.2f}'.format) #2 decimal point for bonus
        else: 
            df['ND'] = df['ND'].map('{:.1f}'.format) #1 decimal point for neutral deductions
            df['Bonus'] = df['Bonus'].map('{:.1f}'.format) #1 decimal point for bonus
        
        # create "Category" column with capital "C" and map the acronyms to the full text
        df['Category'] = df['category'].map(database['category_acronyms'])
        
        # create "Country column"
        df['Country'] = df['country']
        
        # Add rank column
        df['Rank'] = df.index + 1
        
        # Reorder columns
        df = df[['Rank', 'Athlete name', 'Country','Category','D score', 'E score','ND' ,'Bonus','Score']]
        
        # Remove rows where 'E score' is NaN or 0.0
        df_cleaned = df[~(df['E score'].isna() | (df['E score'] == 0.0))]
        df = df_cleaned
        
        # Generate HTML table with highlighted row if a selected athlete is provided
        # table_rows = []
        # for i in range(len(df)):
        #     row_data = df.iloc[i]
        #     background_color = 'yellow' if row_data['Athlete name'] == selected_athlete else ('white' if i % 2 == 0 else '#e6f2ff') #making it blue if not selected
        #     table_row = html.Tr(
        #         [html.Td(row_data[col], style={'background-color': background_color, 'padding': '10px'}) for col in df.columns]
        #     )
        #     table_rows.append(table_row),
        
        # table = html.Table(

        #     [html.Tr([html.Th(col, style={'padding': '10px', 'background-color': '#cce7ff'}) for col in df.columns])] +
        #     # Body
        #     table_rows,
        #     style={'border-collapse': 'collapse', 'width': 'auto'}
            
        # )


        table = dash_table.DataTable(
            columns=[{"name": i, "id": i, "deletable": False} for i in df.columns],
            data=df.to_dict('records'),
            sort_action='native',            # allow sorting
            filter_action='native',          # allow filtering
            # style_data_conditional=style_data_conditional,
            style_header={
                'backgroundColor': '#cce7ff',
                'fontWeight': 'bold',
                'textAlign': 'center',
            },
            # IMPORTANT: try inline-block + width:auto on the table container
            style_table={
                'width': 'auto',            # let table width be its content width
                'minWidth': '0',            # helps prevent flex/min-width issues
                'overflowX': 'auto',
                'display': 'inline-block',   # key: make table act like inline-block within wrapper
                # style_as_list_view=True,
            },
        
            # make cells size to content (use minWidth 0 to avoid forcing stretch)
            style_cell={
                'minWidth': '0px',
                'width': 'auto',
                'maxWidth': '200px',
                'whiteSpace': 'normal',
                'textAlign': 'center',
                'padding': '6px 10px'
            },
    )
    return table

# def update_table(database, competition, categories, results, apparatus, selected_athlete=None):
#     table_data = get_category_data_for_competition_day(database, competition, categories, results, apparatus)
    
#     if not table_data:
#         return dash_table.DataTable()  # empty table
    
#     df = pd.DataFrame.from_dict(table_data, orient='index')

#     # Fill missing columns and NaNs
#     expected_columns = ['Score', 'E', 'D', 'ND', 'Bonus', 'category', 'country']
#     for col in expected_columns:
#         if col not in df.columns:
#             df[col] = 0.0

#     df = df.fillna(0.0)
    
#     # Keep only rows with a valid D  score (not NaN or zero)
#     # sometimes a legitimate score can be zero so best to check
#     # df = df[(df['D'].notna() & (df['D'] != 0)) | (df['E'].notna() & (df['E'] != 0))]
#     df = df[(df['D'].notna() & (df['D'] != 0))]

#     # Format scores
#     df['D score'] = df['D'].map('{:.3f}'.format)
#     df['E score'] = df['E'].map('{:.3f}'.format)
#     df['Score'] = df['Score'].map('{:.3f}'.format)
#     if results == "average":
#         df['ND'] = df['ND'].map('{:.2f}'.format)
#         df['Bonus'] = df['Bonus'].map('{:.2f}'.format)
#     else:
#         df['ND'] = df['ND'].map('{:.1f}'.format)
#         df['Bonus'] = df['Bonus'].map('{:.1f}'.format)

#     # Add extra columns
#     df['Category'] = df['category'].map(database['category_acronyms'])
#     df['Country'] = df['country']
#     df['Athlete name'] = df.index
#     df['Rank'] = range(1, len(df) + 1)

#     # Reorder columns
#     df = df[['Rank', 'Athlete name', 'Country', 'Category', 'D score', 'E score', 'ND', 'Bonus', 'Score']]

#     # Highlight selected athlete
#     style_data_conditional = []
#     if selected_athlete:
#         style_data_conditional = [
#             {
#                 'if': {'filter_query': f'{{Athlete name}} = "{selected_athlete}"'},
#                 'backgroundColor': 'yellow',
#                 'fontWeight': 'bold'
#             }
#         ]

#     # Generate HTML table with highlighted row if a selected athlete is provided
#     #no longer works with filterable data fix #TODO
#     table_rows = []
#     for i in range(len(df)):
#         row_data = df.iloc[i]
#         background_color = 'yellow' if row_data['Athlete name'] == selected_athlete else ('white' if i % 2 == 0 else '#e6f2ff') #making it blue if not selected
#         table_row = html.Tr(
#             [html.Td(row_data[col], style={'background-color': background_color, 'padding': '10px'}) for col in df.columns]
#         )
#         table_rows.append(table_row)


#     table = dash_table.DataTable(
#         columns=[{"name": i, "id": i, "deletable": False} for i in df.columns],
#         data=df.to_dict('records'),
#         sort_action='native',            # allow sorting
#         filter_action='native',          # allow filtering
#         # style_data_conditional=style_data_conditional,
#         style_header={
#             'backgroundColor': '#cce7ff',
#             'fontWeight': 'bold',
#             'textAlign': 'center',
#         },
#         # IMPORTANT: try inline-block + width:auto on the table container
#         style_table={
#             'width': 'auto',            # let table width be its content width
#             'minWidth': '0',            # helps prevent flex/min-width issues
#             'overflowX': 'auto',
#             'display': 'inline-block',   # key: make table act like inline-block within wrapper
#             # style_as_list_view=True,
#         },
    
#         # make cells size to content (use minWidth 0 to avoid forcing stretch)
#         style_cell={
#             'minWidth': '0px',
#             'width': 'auto',
#             'maxWidth': '200px',
#             'whiteSpace': 'normal',
#             'textAlign': 'center',
#             'padding': '6px 10px'
#         },
#         # Hardcode specific widths - doesnt seem respected
#         # style_cell_conditional=[
#         #     {'if': {'column_id': 'athlete'}, 'width': '25%'},
#         #     {'if': {'column_id': 'score'}, 'width': '10%'},
#         #     {'if': {'column_id': 'event'}, 'width': '30%'},
#         #     {'if': {'column_id': 'country'}, 'width': '15%'},
#         # ],

#         # page_size=20                      # optional pagination
#     )
    
#     return table


#quickly sort competition options by date
# Sort competitions by date (newest first)
sorted_competitions = sorted(database['series_dates'].keys(), key=lambda x: datetime.strptime(database['series_dates'][x], '%Y-%m-%d'), reverse=True)

print(f"comp; {sorted_competitions}")
# Create options for competition dropdown
competition_options = [{'label': database['series_acronyms'][comp], 'value': comp} for comp in sorted_competitions]


# Define layout of the app

#I might want to make Cateogry, and other drop downs, multi-select

overview_intro = """
Select the Competition Data you would like to visualize through the dropdown 

"""

overview_layout = html.Div([
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    html.H3('Welcome!'),
    html.P('Stoi Analytics is a sports data analytics project, learn more at our website:'),
    html.A("www.stoianalytics.com", href="https://www.stoianalytics.com/", target="_blank"),
    html.P("Dataset: This data is for the Men's Artistic Gymnastics (MAG) results from the 2025 FIG World Artistic Gymnastics Championships"),
    html.P('note: for any inquiries, please contact info@stoianalytics.com'),

    
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    html.H3('Competition Data Selection'),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Div("Competition:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
                    dcc.Dropdown(
                        id='competition-dropdown',
                        # options=[{'label': database['series_acronyms'][comp], 'value': comp} for comp in database['overview'].keys()],
                        # value=list(next(iter(database.values())).keys())[0],
                        options=competition_options,
                        value=sorted_competitions[0],
                        style=dropdown_style1
                    )
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Div("Category:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
                    dcc.Dropdown(
                        id='category-dropdown',
                        # value='SR21', #initializing with this value for now - should be dynamic
                        style=dropdown_style1,
                        multi=True  # Enable multi-select
                    )
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Div("Results:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
                    dcc.Dropdown(
                        id='results-dropdown',
                        # options=[{'label': tla_dict[app], 'value': app} for app in tlas],
                        # value='average', #initializing with this value for now - should be dynamic
                        style=dropdown_style1
                    
                    )
                ], style={'marginBottom': '10px'}),
                html.Div([
                    html.Div("Apparatus:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
                    dcc.Dropdown(
                        id='apparatus-dropdown',
                        options=[{'label': tla_dict[app], 'value': app} for app in tlas],
                        value='FX',#used to have AA as default but changing for World Cups
                        style=dropdown_style1
                    )
                ], style={'marginBottom': '10px'})
            ])
        ], style={'flex': '0 0 80%'}),  # Adjust width as needed
        
    
    ], style={'display': 'flex', 'alignItems': 'flex-start'}),
    
    
    dcc.Store(id='results-store', data=database),  # Store the database - needed to dynamically change data in dropdown menus
    
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),

    dbc.Container([
        html.H3('Interactive Bubble and  Histogram Plots'),
        
        dbc.RadioItems(
        id='plot-toggle',
        options=[
            {'label': 'Bubble Plot', 'value': 'bubble'},
            {'label': 'Histogram', 'value': 'histogram'}
        ],
        value='bubble',
        inline=True
            ),

        html.Div([
            dcc.Dropdown(
                id='hist-xaxis-toggle',
                options=[
                    {'label': 'Total Score', 'value': 'Score'},
                    {'label': 'D Score', 'value': 'D'},
                    {'label': 'E Score', 'value': 'E'},
                    {'label': 'Bonus', 'value': 'Bonus'},
                    {'label': 'ND', 'value': 'ND'},
                ],
                value='Score',
                style={'width': '75%'}  # keep the width here
            )
        ],
        id='hist-options-row',  # <--- Add this
        style={'display': 'none', 'marginBottom': '10px'}  # initially hidden
        ),
        
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='bubble-plot', config={'responsive': True},),
                # style={'flex': '0 0 80%'},  # Adjust width as needed
                style={'height': '600px', 'width': '80%'}, #trying to keep it big so it doesnt overlap with table
            )
        ], style={'display': 'flex'}),
        
        
        
        # Customized horizontal line to separate sections
        html.Hr(style={'borderTop': '3px solid #bbb'}),
        
        html.H3("Data Table"),
        ###
        html.Div(
            [
                # html.H3("Data Table"),
                # outer flex container centers content:
                html.Div(
                    # inner inline-block prevents flex from stretching the table
                    html.Div(id='table-container', style={'display': 'inline-block'}),
                    style={'display': 'flex', 'justifyContent': 'center', 'width': '100%'}
                ),
                # html.P('note: for any inquiries, please contact info@stoianalytics.com'),
                html.Hr(style={'borderTop': '3px solid #bbb'}),
            ],
            style={'boxSizing': 'border-box', 'width': '80%'}
        ),
        #####
    ], 
    style={'boxSizing': 'border-box', 'position': 'relative', 'width': '100%', 'height': '0', 'paddingBottom': '60%'}),
    # style={'boxSizing': 'border-box', 'width': '100%'}),
    
])
    
#callback for histogram dropdown to appear when toggle is selected
@app.callback(
    Output('hist-options-row', 'style'),
    Input('plot-toggle', 'value')
)
def toggle_hist_options(plot_type):
    if plot_type == 'histogram':
        return {'display': 'flex', 'width': '75%'}
    return {'display': 'none'}


    
# Define callback to update the options of the results dropdown based on the selected competition and category
@app.callback(
    Output('results-dropdown', 'options'),
    [Input('competition-dropdown', 'value'),
     Input('category-dropdown', 'value')],
    [State('results-store', 'data')]
)
def update_results_dropdown(competition, categories, database):
    # print("Competition:", competition)
    # print("Categories:", categories)
    # print("Database:", database)
    
    #category is now a multi-select option
    #will need to only show the results options that correspond to multi categories
    if competition and categories:
        results_options = []
        #although categories should be a list, sometimes it returns just one
        #lets make sure it is a list if its not
        if not isinstance(categories, list):
            categories = [categories]
            
        for category in categories:
            # print(f"category: {category}")
            # Get the available results options from the database dictionary
            options = database['overview'][competition][category] 
            results_options.append(options)
        #now, only keep the options that show up for all categories
        # print(f"result_options: {results_options}")
        # Create options for the results dropdown
        
    
        def find_common_elements(list_of_lists):
            # Convert each sublist to a set
            sets = [set(sublist) for sublist in list_of_lists]
            
            # Find the intersection of all sets
            common_elements = set.intersection(*sets)
            
            # Convert the result back to a list
            return sorted(common_elements)
        
        common_elements = find_common_elements(results_options)
        # print(common_elements)
        
        #need to show the acronyms of these common elements - right now it breaks the selection
        common_acronyms = [database['competition_acronyms'][c] for c in common_elements]
        
        return [{'label': result, 'value': result} for result in common_elements + ["average","best","combined"]]
    else:
        return []

# Define callback to set the value of the results dropdown to the first option when the competition or category changes
@app.callback(
    Output('results-dropdown', 'value'),
    [Input('competition-dropdown', 'value'),
     Input('category-dropdown', 'value')],
    [State('results-dropdown', 'options')]
)
def set_results_dropdown_value(competition, category, options):
    if options:
        return options[0]['value']
    else:
        return None

# Define callback to update the options of the category dropdown based on the selected competition
@app.callback(
    Output('category-dropdown', 'options'),
    [Input('competition-dropdown', 'value')],
    [State('results-store', 'data')]
)
def update_category_dropdown(competition, database):
    if competition:
        category_options = database['overview'][competition].keys()
        # Create options for the results dropdown
        return [{'label': database['category_acronyms'][category], 'value': category} for category in category_options]
    else:
        return []

# Define callback to set the value of the category dropdown to the first option when the competition changes
@app.callback(
    Output('category-dropdown', 'value'),
    [Input('competition-dropdown', 'value')],
    [State('category-dropdown', 'options')]
)
def set_category_dropdown_value(competition, options):
    if options:
        return options[0]['value']
    else:
        return None


# Define callback to update the bubble plot and table based on selected options

@app.callback(
    [Output('bubble-plot', 'figure'),
     Output('table-container', 'children')],
    [Input('results-dropdown', 'value'),
     Input('apparatus-dropdown', 'value'),
     Input('category-dropdown', 'value'),
     Input('competition-dropdown', 'value'),
     Input('bubble-plot', 'clickData'),# Add clickData as input
     Input('plot-toggle', 'value'),# Add toggle option
     Input('hist-xaxis-toggle', 'value'),# Add toggle option
     ]  
)


def update_plot_and_table(results, apparatus, categories, competition, clickData, plot_type,xaxis_var):
    # Update bubble plot
    # print(f"plot and table categories: {categories}")
    
    #need to make sure categories is a list, it should  be sometimes isn't
    if not isinstance(categories, list):
        categories = [categories]
    
    
    if plot_type == 'bubble':

        data = update_bubble_plot(database, competition, categories, results, apparatus)
        
        #Adding full category name in the data
        #ordered dict seems to be needed to make sure when i convert from ar=cronym to name the order stays the same
        mapped_data = OrderedDict()
        
        if data['x']:
            for key, values in data.items():
                if key == 'category':
                    mapped_data['category'] = []
                    for value in values:
                        mapped_data['category'].append(database['category_acronyms'].get(value, value))
                else:
                    mapped_data[key] = values
        
            # print(f"mapped_data: {mapped_data}")
        
            # Let's use this new mapped data!
            data = mapped_data
            # print(f"data: {data}")
            
        fig = px.scatter(data, x='x', y='y', color='color', size='size', hover_name='name',
                         color_continuous_scale='Viridis', opacity=0.6, hover_data={'name': True,'category':True,'ND': True, 'Bonus': True, 'x': False, 'y': False, 'size': False})
        fig.update_layout(title=f"{database['series_acronyms'][competition]}: D score vs. E score for {tla_dict[apparatus]}", 
                          xaxis_title="Execution (E score)", 
                          yaxis_title="Difficulty (D score)", 
                          autosize=True,
                          margin=dict(l=40, r=40, t=40, b=40),
                          # width=1000, #play with this value until you like it
                          height=600,
                          # width='100%',  # Set width to 100% for responsiveness
                          # aspectratio=dict(x=3, y=2)  # Set aspect ratio (3:2)
                          
                          )
        fig.update_traces(text=data['score'], textposition='top center')  
    
        # Customize hover template
        hover_template = (
            "<b>%{hovertext}</b><br>" +
            "Category: %{customdata[0]}<br>" +
            "D score: %{y:.3f}<br>" +
            "E score: %{x:.3f}<br>" +
            "ND: %{customdata[1]:.1f}<br>" +
            "Bonus: %{customdata[2]:.1f}<br>" +
            "Score: %{text:.3f}"
        )
        # Ensure customdata is a list of [category, ND] pairs for each point
        #convert nan values for ND and Bonus
        data['ND'] = [0.0 if np.isnan(v) else v for v in data['ND']]
        data['Bonus'] = [0.0 if np.isnan(v) else v for v in data['Bonus']]
        
        customdata = list(zip(data['category'], data['ND'], data['Bonus']))
        fig.update_traces(hovertemplate=hover_template, customdata=customdata)
        
        # Update color bar legend
        fig.update_coloraxes(colorbar_title="Score")
        
        # Map color values to score values for color bar tick labels
        color_values = np.linspace(0, 1, 11)  
        
        #only try to get a max score if we have plottable data, otherwise set max_score to an arbitrary value
        if not data['x']:
            max_score = 16
        else:
            max_score = np.nanmax(data['score'])
            # print(f"max score: {max_score}")
            score_values = [value * max_score for value in color_values]  
            # print(f"score values: {score_values}")
            
            # Update color bar tick labels
            fig.update_coloraxes(colorbar_tickvals=color_values, colorbar_ticktext=[f"{score:.3f}" for score in score_values])
        
        # If a point is clicked, highlight the corresponding row in the table
        if clickData:
            try:
                selected_athlete = clickData['points'][0]['hovertext']
                table = update_table(database, competition, categories, results, apparatus, selected_athlete)
            except:
                table = update_table(database, competition, categories, results, apparatus)
        else:
            table = update_table(database, competition, categories, results, apparatus)
    
    elif plot_type == 'histogram':
        fig = update_histogram(database, competition, categories, results, apparatus,xaxis_var)
        table = update_table(database, competition, categories, results, apparatus)
    
    return fig, table


########################################
#%% Tab 2: Individual Athlete Analysis #
########################################

#colour dictionary

barplot_colours = {'D':
                       ['rgb(31, 119, 180)',  # Blue
                        'rgb(255, 127, 14)',  # Orange
                        'rgb(44, 160, 44)',   # Green
                        'rgb(214, 39, 40)',   # Red
                        'rgb(148, 103, 189)', # Purple
                        'rgb(140, 86, 75)',   # Brown
                        'rgb(227, 119, 194)'  # Pink
                        ]
                        ,
                   'E':
                       ['rgba(31, 119, 180, 0.5)',  # Light Blue
                        'rgba(255, 127, 14, 0.5)',  # Light Orange
                        'rgba(44, 160, 44, 0.5)',   # Light Green
                        'rgba(214, 39, 40, 0.5)',   # Light Red
                        'rgba(148, 103, 189, 0.5)', # Light Purple
                        'rgba(140, 86, 75, 0.5)',   # Light Brown
                        'rgba(227, 119, 194, 0.5)'  # Light Pink
                        ]
                     }
    
import colorsys

def generate_bonus_color(base_hex, brighten_factor=1.3, saturate_factor=1.2):
    # Convert hex → RGB (0–1 range)
    base_hex = base_hex.lstrip('#')
    r, g, b = tuple(int(base_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    
    # Convert RGB → HLS
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    
    # Brighten and saturate
    l = min(1.0, l * brighten_factor)
    s = min(1.0, s * saturate_factor)
    
    # Convert back → RGB
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    
    # Return as hex
    return '#{:02X}{:02X}{:02X}'.format(int(r * 255), int(g * 255), int(b * 255))
   
    

def barplot_width(n):
    if n == 1:
        width = 0.4
    elif n ==2:
        width = 0.3
    elif n == 3:
        width = 0.225
    elif n==4:
        width = 0.175
    elif n==5:
        width = 0.175/2.2
    elif n==5:
        width = 0.175/4.5
    else:
        width=0.0
    return width

# Define layout for the second tab with dropdowns and bar graph


#SUBPLOT CODE

# Define function to generate subplot based on athlete dropdown selection change
def generate_subplot(athlete):
    
    #start by intitiating plot
    # Create subplot with independent y-axes
    fig = make_subplots(rows=7, cols=1, shared_xaxes=True) #, subplot_titles=tlas)
    
    #if we've selected an athlete, then proceed
    if athlete and athlete not in exclude_keys:
        # print(f"athlete: {athlete}")
        #get competitions
        #Also Sketchy, hardcoding series and category
        #TODO
        # competitions = database[athlete]["WorldChamps2025"].keys()
        exclusions = ["category", "country", "average", "best", "combined"]
        competitions = [k for k in database[athlete]["WorldChamps2025"].keys() if k not in exclusions]
        comp_days_date = []
        # i = 0 #temporary date counter
        for comp in competitions:
            #also sketchy, hard coding in competition seroies
            results = [key for key in database[athlete]['WorldChamps2025'].keys() if key not in ["category", "average", "best","combined"]]
            for day in results:
                date = database['competition_dates'][comp]
                comp_days_date.append([comp,comp,date])
                

        #re-order based on date and comeptition date
        # Define the secondary sort order
        secondary_sort_order = {'day1': 1, 'day2': 2, 'day3': 3, 'day4': 4,#if format is days
                                'QF': 1, 'TF': 2, 'AA': 3, 'EF': 4, #if format is qualifying, team final, aa final, event final
                                }
        
        print(comp_days_date)
        
        # Sort the list of lists by the date (primary key) and then by the secondary key
        # comp_days_date_sorted = sorted(comp_days_date, key=lambda x: (datetime.strptime(x[2], '%Y-%m-%d'),secondary_sort_order[x[1]]))
        
    
        #only gonna sort once now
        comp_days_date_sorted = sorted(comp_days_date, key=lambda x: (datetime.strptime(x[2], '%Y-%m-%d'))) #,secondary_sort_order[x[1]]))
        
        # print(comp_days_date_sorted)
        
        scores = {}
        categories = []
        comp_labels = []
        for tla in tlas:
            tla_data = []
            for comp,day,date in comp_days_date_sorted:
                # print(f"comp: {comp}, day: {day}, date: {date}")
                # comp_labels.append(comp+" ("+day+")")
                #^right now comp and day returning same value so changing
                comp_labels.append(comp)
                score = database[athlete]['WorldChamps2025'][comp][tla]['Score']
                categories.append(database[athlete]['WorldChamps2025']['category'])
                if score == 0:
                    score = np.nan #set to nan
                tla_data.append(score)
            scores[tla] = tla_data
            
    
        # Create traces for each TLA
        traces = []
        for tla in tlas:
            max_score = np.nanmax(scores[tla])
            min_score = np.nanmin(scores[tla])
            score_range = max_score - min_score
            trace = go.Scatter(
                x=comp_labels,
                y=scores[tla],
                mode='lines+markers+text',
                name=tla,
                hoverinfo='text',  # Set hover info to only display text,
                hovertext=[f"{database['category_acronyms'][category]}" for category in categories],
                text=[f"{score}" for score in scores[tla]],
                # text=
                textposition=['top center' if score - min_score < score_range * 0.5 else 'bottom center' for score in scores[tla]]  # Adjust textposition based on y-axis position
                # name=None,
            )
            traces.append(trace)
    
        # Add traces to subplot
        for i, trace in enumerate(traces): 
            fig.add_trace(trace, row=i + 1, col=1)
    
        # Update layout settings
        fig.update_layout(
            title=f'{athlete} Competition Scores',
            # xaxis=dict(title='Competitions'),
            # width=1000,
            height=800,
            showlegend=False,
            margin=dict(l=40, r=200, t=40, b=40)  # Adjust the margins as needed
        )
        
        # Remove the x-axis title for the first subplot
        fig.update_xaxes(title='', row=1, col=1)
        # fig.update_xaxes(title='Competitions', row=7, col=1)
        
        # add x-axis and y axis labels 
        for i in range(1, 8): #used to have 9, changed as we dropped AA
            fig.update_xaxes(showticklabels=True, row=i, col=1)
            fig.update_yaxes(title=tlas[i-1], row=i, col=1)
    else:
        fig.update_layout(
            title=f'Select an Athlete to see their Competition Scores',
            # xaxis=dict(title='Competitions'),
            # width=1000,
            height=800,
            showlegend=False,
            margin=dict(l=40, r=200, t=40, b=40)  # Adjust the margins as needed
        )
        # Remove the x-axis title for the first subplot
        fig.update_xaxes(title='', row=1, col=1)
        # fig.update_xaxes(title='Competitions', row=7, col=1)
        
        # Create traces for each TLA
        traces = []
        for tla in tlas:
            trace = go.Scatter()
            traces.append(trace)
    
        # Add traces to subplot
        for i, trace in enumerate(traces): 
            fig.add_trace(trace, row=i + 1, col=1)
        
        
        # add x-axis and y axis labels 
        for i in range(1, 8): #changed from 9 to 8 when dropped AA for world cups
            fig.update_xaxes(showticklabels=False, row=i, col=1)
            fig.update_yaxes(title=tlas[i-1], row=i, col=1)
            
    return fig

#legend for apparatus names
# Function to create legend items
def create_apparatus_legend(tla_dict):
    return html.Ul([html.Li(f"{tla}: {description}") for tla, description in tla_dict.items()])
def create_competition_legend(competition_acronyms):
    return html.Ul([html.Li(f"{abbreviation}: {competition}") for abbreviation, competition in competition_acronyms.items()])
    # ^ current dataset has abbreviation and competition as same so just removing it for now
    # return html.Ul([html.Li(f"{abbreviation}") for abbreviation, competition in competition_acronyms.items()])


tab2_layout = html.Div([
    
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    
    html.H3('Plot Athlete Scores Across Competition Days'),
    
    html.Div([
        html.Div("Athlete", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
        dcc.Dropdown(
            id='athlete-dropdown2',
            # options = [{'label': athlete, 'value': athlete} for athlete in database.keys() if athlete not in exclude_keys],
            # value=next(iter(database)),  # Default value
            options=[{'label': athlete, 'value': athlete} for athlete in sorted(database.keys()) if athlete not in exclude_keys],
            # value=sorted([athlete for athlete in database.keys() if athlete not in exclude_keys])[0],  # Default value as the first alphabetically sorted athlete
            value = None,
            multi=False,  # Single select
            style=dropdown_style2
        ),
    ]),
    
    # Subplot will be added here based on athlete dropdown selection change
    dcc.Graph(id='subplot'),
    
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),

    html.H3('Score Breakdown by Competition'),
    
    # html.P("Follow these steps to use the Score Breakdown Plot:"),
    # html.Ol([
    #     html.Li("Use the Competition and Results dropdowns to filter the score breakdown by specific competitions and results."),
    #     html.Li("Hover over the bars in the score breakdown plot to see detailed D and E scores for each apparatus."),
    #     html.Li("Click on the toolbar above the plots to save the plot as an image, zoom in or out, and crop specific sections of the plot for a closer view.")
    # ]),
    
    
    html.Div([
        html.Div("Competition", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
        dcc.Dropdown(
            id='competition-dropdown2',
            # options=[{'label': database['competition_acronyms'][comp], 'value': comp} for comp in database['overview'].keys()],
            value=list(next(iter(database.values())).keys())[0],
            multi=True, #New
            style=dropdown_style2
        ),
        
    ]),
    # dcc.Store(id='results-store2', data=database),  # Store the database - needed to dynamically change data in dropdown menus
    dcc.Graph(id='score-graph'), #, style={'width': '1000px', 'height': '400px'}),
    
])

#PLOT 1 CALLBACKS

@app.callback(
    [Output('competition-dropdown2', 'options'),
     Output('competition-dropdown2', 'value')],
    [Input('athlete-dropdown2', 'value')]
)
def update_competition_dropdown(athlete):
    if athlete:
        exclusions = ["category","country", "average", "best", "combined"]
        competitions = [k for k in database[athlete]["WorldChamps2025"].keys() if k not in exclusions]
        comp_options = [{'label': database['competition_acronyms'][comp], 'value': comp} for comp in competitions]
        return comp_options, None
    else:
        return [], None

@app.callback(
    Output('score-graph', 'figure'),
    [Input('athlete-dropdown2', 'value'),
     Input('competition-dropdown2', 'value')]
)

def update_score_graph(athlete, competition):
    traces = []
    max_score = 0

    #lets check to see if we have everythin selected
    if athlete and competition:
        
        #lets make sure it is a list if its not make it one
        if not isinstance(competition, list):
            competition = [competition]
        
        #width and offset will be based on number of days selected
        # n_days = len(results)
        # print(f"n_days: {n_days}")
        
        n_comps = len(competition)
        width = barplot_width(n_comps)
        offset_multiplier = -width * (n_comps - 1) / 2  # Start around center
        
        for i, comp in enumerate(competition):
        
            # athlete = database[athlete][competition]
            d_scores = []
            e_scores = []
            total_scores = []
            ND_scores = []
            Bonus_scores = []
            plot_apparatus = ['FX','PH','SR','VT1','VT2','PB','HB']
            # plot_apparatus = ['FX','PH','SR','VT1','PB','HB']
            
            for app in plot_apparatus:
                d_scores.append(database[athlete][SERIES][comp][app]['D'])
                e_scores.append(database[athlete][SERIES][comp][app]['E'])
                total_scores.append(database[athlete][SERIES][comp][app]['Score'])
                ND_scores.append(database[athlete][SERIES][comp][app]['ND'])
                Bonus_scores.append(database[athlete][SERIES][comp][app]['Bonus'])
                
                # max_score = 16 #max(max_score, max(database[athlete][competition][result][app]['Score'])) #+athlete[day][app]['E'])) #, athlete[day][app]['E']))
                score = database[athlete][SERIES][comp][app]['Score']
                if score > max_score:
                    max_score = score
            # print(generate_bonus_color(barplot_colours['E'][i]))
            
            #get rid of nans
            Bonus_scores = [0 if np.isnan(B) else B for B in Bonus_scores]
            ND_scores = [0 if np.isnan(ND) else ND for ND in ND_scores]
            # Create stacked bar trace for D and E scores and Bonus
            
            stacked_trace_Bonus = go.Bar(
                # x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
                x=[j + offset_multiplier for j in range(len(plot_apparatus))],

                y=Bonus_scores,
                name="Bonus",#f'Bonus ({comp})',
                # hoverinfo='y+name',
                hovertext=[f'{B:.3f}' for B in Bonus_scores],
                hoverinfo='text+name',  # Use custom hover text and show trace name
                
                # marker_color = "#FFD700",#gold, bright
                marker=dict(
                    color="#3CB371",           # gold fill
                    # line=dict(
                    #     color='black',         # border color
                    #     width=1.2              # border thickness
                    # )
                    # line=dict(color="#3CB371")
                    line=dict(color="#3CB371", width=1)  # <-- border of the bars
                ),
                # bonus_green = "#3CB371"  # MediumSeaGreen

                # marker_color = generate_bonus_color(barplot_colours['E'][i]),# Set color for Bonus scores
                # marker_pattern='cross',
                # marker=dict(pattern='+', pattern_fgcolor='black'),
                # marker_pattern_fgcolor=barplot_colours['E'][day],
                # offsetgroup=comp,  # Group by day
                legendgroup=comp,  # Group by day
                # legendgroup="Bonus",  # Group by day
                # base=d_scores,  # Offset by D scores
                width = width,
                showlegend=(i==0)  # Only show for the first competition
            )
            
            stacked_trace_d = go.Bar(
                # x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
                x=[j + offset_multiplier for j in range(len(plot_apparatus))],

                y=d_scores,
                name=f'D score ({comp})',
                # hoverinfo='y+name',
                hovertext=[f'{d:.3f}' for d in d_scores],
                hoverinfo='text+name',  # Use custom hover text and show trace name
                
                marker_color=barplot_colours['D'][i],  # Set color for D scores
                # marker_pattern='cross',
                # marker=dict(pattern='+', pattern_fgcolor='black'),
                # marker_pattern_fgcolor=barplot_colours['E'][day],
                # offsetgroup=comp,  # Group by day
                legendgroup=comp,  # Group by day
                base=Bonus_scores,#offset with bonus scores now
                width = width,
            )
            
            
            
            stacked_trace_e = go.Bar(
                # x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
                x=[j + offset_multiplier for j in range(len(plot_apparatus))],
                y=e_scores,
                name=f'E score ({comp})',
                #custom hover text
                # hoverinfo='y+name',
                hovertext=[f'{e:.3f}' for e in e_scores],
                hoverinfo='text+name',  # Use custom hover text and show trace name
                
                marker_color=barplot_colours['E'][i],  # Set color for E scores
                # offsetgroup=comp,  # Group by day
                legendgroup=comp,  # Group by day
                # base=d_scores+Bonus_scores,  # Offset by D scores + Bonus scores
                base=[d + B for d, B in zip(d_scores, Bonus_scores)],
                width = width,
                # Adding text above the bar plot for the whole score, truncated to 3 decimal places
                text=[f'{d + e + B + ND:.3f}' for d, e, B, ND in zip(d_scores, e_scores, Bonus_scores, ND_scores)],
                textposition='outside'
            )
            
            stacked_trace_ND = go.Bar(
                # x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
                x=[j + offset_multiplier for j in range(len(plot_apparatus))],
                y=ND_scores,
                name="ND", #({comp})',
                #custom hover text
                # hoverinfo='y+name',
                hovertext=[f'{ND:.3f}' for ND in ND_scores],
                hoverinfo='text+name',  # Use custom hover text and show trace name
                
                # marker_color='rgba(255,0,0,0.4)',  # semi-transparent red
                marker_color='rgba(255,0,0,1.0)',  # bright opaque red
                # offsetgroup=comp,  # Group by day
                legendgroup=comp,  # Group by day
                # legendgroup="Bonus",  # Group with Bonus
                # base=d_scores+Bonus_scores+e_scores,  # Offset by D scores + Bonus scores + E scores
                base=[d + e + B for d, e, B in zip(d_scores, e_scores, Bonus_scores)],  # element-wise sum
                width = width,
                # Adding text above the bar plot for the whole score, truncated to 3 decimal places
                # text=[f'{d + e + B - ND:.3f}' for d, e, B, ND in zip(d_scores, e_scores, Bonus_scores, ND_scores)],
                # textposition='outside'
                showlegend=(i==0)  # Only show for the first competition
            )
            
            traces.append(stacked_trace_Bonus)
            traces.append(stacked_trace_ND)
            traces.append(stacked_trace_d)
            traces.append(stacked_trace_e)
            
            
            
            
            # Increment the offset multiplier for the next day
            offset_multiplier += width # Adjust the multiplier as needed to prevent overlapping bars
        
        layout = go.Layout(
        title=f'Score Breakdown for {athlete} at {database["series_acronyms"][SERIES]}',
        xaxis={'title': 'Apparatus'},
        yaxis={'title': 'Score', 'range': [0, max_score * 1.1]},
        barmode='relative',  # Relative bars for stacked and grouped
        # width=1000,
        height=600
        )
    
        # Set x-axis tick labels to be the apparatus names
        layout['xaxis']['tickvals'] = list(range(len(plot_apparatus)))
        layout['xaxis']['ticktext'] = plot_apparatus
        # print(f"plot app: {plot_apparatus}")
    else:
        #if we havent selected valid inputs yet, return blank
        traces = [go.Bar()]
        layout = go.Layout()
        
    return {'data': traces, 'layout': layout}

# def update_score_graph(athlete, competition):
#     traces = []
#     max_score = 0

#     if athlete and competition:
#         d_scores = []
#         e_scores = []
#         plot_apparatus = ['FX','PH','SR','VT1','VT2','PB','HB']
        
#         for app in plot_apparatus:
#             d = database[athlete][SERIES][competition][app]['D']
#             e = database[athlete][SERIES][competition][app]['E']
#             score = database[athlete][SERIES][competition][app]['Score']
            
#             d_scores.append(d)
#             e_scores.append(e)
#             if score > max_score:
#                 max_score = score

#         # width = barplot_width(1)  # You now always have one bar per apparatus
#         width = 0.4  # or hardcode as fixed

#         stacked_trace_d = go.Bar(
#             x=list(range(len(plot_apparatus))),
#             y=d_scores,
#             name='D score',
#             hovertext=[f'{d:.3f}' for d in d_scores],
#             hoverinfo='text+name',
#             marker_color=barplot_colours['D'][0],
#             width=width
#         )

#         stacked_trace_e = go.Bar(
#             x=list(range(len(plot_apparatus))),
#             y=e_scores,
#             name='E score',
#             hovertext=[f'{e:.3f}' for e in e_scores],
#             hoverinfo='text+name',
#             marker_color=barplot_colours['E'][0],
#             base=d_scores,
#             width=width,
#             text=[f'{d + e:.3f}' for d, e in zip(d_scores, e_scores)],
#             textposition='outside'
#         )

#         traces = [stacked_trace_d, stacked_trace_e]

#         layout = go.Layout(
#             title=f'Score Breakdown for {athlete} at {database["competition_acronyms"][competition]}',
#             xaxis={'title': 'Apparatus'},
#             yaxis={'title': 'Score', 'range': [0, max_score * 1.1]},
#             barmode='relative',
#             height=400,
#             xaxis_tickvals=list(range(len(plot_apparatus))),
#             xaxis_ticktext=plot_apparatus
#         )
#     else:
#         traces = [go.Bar()]
#         layout = go.Layout()

#     return {'data': traces, 'layout': layout}


#SUBPLOT CALLBACKS

# Callback to update the subplot based on athlete dropdown selection change
@app.callback(
    Output('subplot', 'figure'),
    [Input('athlete-dropdown2', 'value')]
)
def update_subplot(athlete):
    return generate_subplot(athlete)


#############################
#%% Tab 3: Team Scenarios ###
#############################

#TODO: if number of athletes in a category < format needs or scenarios avaialble for that format, return some error.

# # Header for the table
# display_header = ['Athlete', 'FX', 'PH', 'SR', 'VT', 'PB', 'HB', 'AA']
# header = ['Athlete', 'FX', 'FX_status', 'PH', 'PH_status', 'SR', 'SR_status', 'VT', 'VT_status', 'PB', 'PB_status', 'HB', 'HB_status', 'AA']


# def generate_table(data):
#     return dash_table.DataTable(
#         columns=[{'name': i, 'id': i} for i in header],
#         data=data,
#         style_cell={'textAlign': 'center', 'whiteSpace': 'normal', 'height': 'auto'},  # Ensure text wraps within cells
#         style_table={'overflowX': 'auto'},  # Enable horizontal scroll if content overflows
#     )


# Header for the table
header = ['Athlete', 'FX', 'PH', 'SR', 'VT1', 'PB', 'HB', 'AA']
# header = ['Athlete', 'FX', 'FX_status', 'PH', 'PH_status', 'SR', 'SR_status', 'VT', 'VT_status', 'PB', 'PB_status', 'HB', 'HB_status', 'AA']

# Define the color dictionary
colour_dict = {"dropped": "#FFFFCC", "scratch": "grey", "counting": "green"}

# Define hidden columns and conditional formatting based on status
hidden_columns = [f'{event}_status' for event in ['FX', 'PH', 'SR', 'VT1', 'PB', 'HB']]
style_data_conditional = []

for event in ['FX', 'PH', 'SR', 'VT1', 'PB', 'HB']:
    for status, color in colour_dict.items():
        style_data_conditional.append(
            {
                'if': {
                    'filter_query': f'{{{event}_status}} = "{status}"',
                    'column_id': event
                },
                'backgroundColor': color,
                'color': 'white' if color not in ['white',colour_dict['dropped']] else 'black',
            }
        )


# # Function to generate the table
# def generate_table(data):
#     return dash_table.DataTable(
#         columns=[{'name': i, 'id': i, 'hideable': False} for i in header],
#         # columns=[{'name': i, 'id': i} for i in header],
#         data=data,
#         style_cell={'textAlign': 'center', 'whiteSpace': 'normal', 'height': 'auto'},  # Ensure text wraps within cells
#         style_table={'overflowX': 'auto'},  # Enable horizontal scroll if content overflows
#         style_data_conditional=style_data_conditional,
#         hidden_columns=hidden_columns,
#         # config={'modeBarButtonsToAdd': []}  # Disable the "toggle columns" option
#     )

# # Header for the table
# display_header = ['Athlete', 'FX', 'PH', 'SR', 'VT', 'PB', 'HB', 'AA']
# header = ['Athlete', 'FX', 'FX_status', 'PH', 'PH_status', 'SR', 'SR_status', 'VT', 'VT_status', 'PB', 'PB_status', 'HB', 'HB_status', 'AA']

# Define which columns will have filtering enabled
# filterable_columns = ['FX', 'PH', 'SR', 'VT', 'PB', 'HB', 'AA']

# Create a list of column definitions
# columns = [{'name': i, 'id': i, 'hideable': False} for i in header]
columns = [{'name': i, 'id': i} for i in header]

# # Enable filtering for filterable columns
# for col in columns:
#     if col['id'] in filterable_columns:
#         col['filter_options'] = {'case': 'sensitive', 'clearable': True, 'className': 'dropdown'}

def generate_table(data):
    return dash_table.DataTable(
        columns=columns,
        data=data,
        style_cell={'textAlign': 'center', 'whiteSpace': 'normal', 'height': 'auto'},  # Ensure text wraps within cells
        style_table={'overflowX': 'auto'},  # Enable horizontal scroll if content overflows
        style_data_conditional=style_data_conditional,
        # hidden_columns=hidden_columns,
        
    )

colour_dict = {"dropped": "#FFFFCC", "scratch": "grey", "counting": "green"}

# Define the legend data
# legend_data = [
#     {"Status": "Counting Score", "Description": colour_dict['counting']},
#     {"Status": "Dropped Score", "Description": colour_dict['dropped']},
#     {"Status": "Scratch (would not compete)", "Description": colour_dict['scratch']},
# ]

legend_data = [
    {"Status": "Counting", "Description": "the athlete competes and the score contributes to the Team Total"},
    {"Status": "Dropped", "Description": "the athlete competes but the score does not contribute to the Team Total"},
    {"Status": "Scratch", "Description": "the athlete would not compete and the score would not contribute to the Team Total"},
]

# Define the text color based on background color
text_color_dict = {"counting": "white", "dropped": "black", "scratch": "white"}

# Style for the legend table
style_data_conditional_legend = []

for status, bg_color in colour_dict.items():
    text_color = text_color_dict[status]
    style_data_conditional_legend.append(
        {
            'if': {
                'filter_query': f'{{Status}} = "{status.capitalize()}"',
                'column_id': 'Status'
            },
            'backgroundColor': bg_color,
            'color': text_color,
        }
    )

tab3_layout = html.Div([
    
    html.H3("How to Use The Team Scenarios Analysis Tab"),
    html.P("Follow these steps to interact with the data:"),
    html.Ol([
        html.Li("Select a competition from the dropdown."),
        html.Li("Choose one or more categories of athletes to include in the analysis."),
        html.Li("Select specific results to analyze (ex. average, best, combined, etc.)."),
        html.Li("Define the competition format by entering the number of competitors per apparatus."),
        html.Li("Set the number of top team scenarios you want to calculate and view."),
        html.Li("Click the 'Calculate' button to generate and view the team scenarios based on your selections."),
        html.Li("The results will display the top team scenarios with scores for each apparatus and overall team scores."),
    ]),
    
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    
    
    html.H3('Make Selections for Top Team Scores Calculations'),
    dbc.Row([
        dbc.Col([
            html.Div("Competition", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
            dcc.Dropdown(
                id='competition-dropdown3',
                # options=[{'label': database['competition_acronyms'][comp], 'value': comp} for comp in database['overview'].keys()],
                # value=list(next(iter(database.values())).keys())[0],
                options=competition_options,
                value=sorted_competitions[0],
                style=dropdown_style2
            ),
        ], width=6),
        dbc.Col([
            html.Div("Category:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
            dcc.Dropdown(
                id='category-dropdown3',
                style=dropdown_style2,
                # value = "SR21",
                multi=True  # Enable multi-select
            ),
        ], width=6),
        dbc.Col([
            html.Div("Results:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
            dcc.Dropdown(
                id='results-dropdown3',
                style=dropdown_style2
            ),
        ], width=6),
    ]),
    dcc.Store(id='results-store3', data=database),  # Store the database - needed to dynamically change data in dropdown menus
    
    # html.Hr(style={'borderTop': '3px solid #bbb'}),
    
    # html.H3('Select Competition Format'),
    html.Div("Competition Format (max 5 athletes):", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
    
    html.Div([
        dcc.Input(id='xx-input', type='number', min=1, max=5, value=5, style={'width': '50px', 'fontSize': '16px'}),
        html.Label('-', style={'padding': '0 5px'}),  # Added label with padding
        dcc.Input(id='yy-input', type='number', min=1, max=5, value=4, style={'width': '50px',  'fontSize': '16px'}),
        html.Label('-', style={'padding': '0 5px'}),  # Added label with padding
        dcc.Input(id='zz-input', type='number', min=1, max=5, value=3, style={'width': '50px', 'fontSize': '16px'}),
        html.Div("(Team Size - Competitors per Apparatus - Counting Scores per Apparatus)", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
    ]),
    
    html.Label('Show Top', style={'margin-top': '10px'}),  # Added label for the top X team scenarios
    dcc.Input(id='top-x-input', type='number', min=1, max=20, value=5, style={'width': '50px', 'fontSize': '16px'}),  # Added input box for X
    html.Label('team scenarios', style={'margin-left': '5px', 'margin-top': '10px'}),  # Added label for team scenario
    
    
    html.Button('Calculate', id='calculate-button', n_clicks=0, style={'display': 'block', 'margin-top': '10px', 'width': '150px', 'height': '40px', 'background-color': 'green', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'}),
    
    #Add a note saying it could take a while to generte
    html.H4('(note: depending on the number of athletes in a category, results could take a while to load... thank you for your patience)', style={'margin-top': '10px'}),
    
    #Alert container
    html.Div(id='alert-container'),
    
    html.Div(id='progress-container'),
    dcc.Interval(id='progress-interval', interval=500, n_intervals=0,disabled=True),  # 500 ms interval for progress updates
    
    
    
    # Container for the progress spinner and tables- add CSS formating to make sure the spinner/loading element is at the top of the table
    html.Div(id='progress-tables-container', children=[
        dcc.Loading(
            id='loading-spinner',
            # type='circle', #options:'graph', 'cube', 'circle', 'dot' or 'default'; 
            type='dot',
            children=[html.Div(id='tables-container')],
            style={'position': 'absolute', 'top': '0', 'left': '50%', 'transform': 'translateX(-50%)'},
        )
    ], style={'position': 'relative'}),
    
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    # Legend
    html.Div(
        [
            html.H3('Table Legend'),
            dash_table.DataTable(
                columns=[{"name": "Status", "id": "Status"}, {"name": "Description", "id": "Description"}],
                data=legend_data,
                style_table={"margin-top": "10px"},
                style_cell={"textAlign": "center", "whiteSpace": "normal", "height": "auto"},
                style_data_conditional=style_data_conditional_legend,
            ),
        ],
        style={"margin-bottom": "20px"},
    ),
    
])

# Define callback to update the options of the results dropdown based on the selected competition and category
@app.callback(
    Output('results-dropdown3', 'options'),
    [Input('competition-dropdown3', 'value'),
     Input('category-dropdown3', 'value')],
    [State('results-store3', 'data')]
)
def update_results_dropdown(competition, categories, database):
    # print("Competition:", competition)
    # print("Categories:", categories)
    # print("Database:", database)
    
    #category is now a multi-select option
    #will need to only show the results options that correspond to multi categories
    if competition and categories:
        results_options = []
        #although categories should be a list, sometimes it returns just one
        #lets make sure it is a list if its not
        if not isinstance(categories, list):
            categories = [categories]
            
        for category in categories:
            # print(f"category: {category}")
            # Get the available results options from the database dictionary
            options = database['overview'][competition][category] 
            results_options.append(options)
        #now, only keep the options that show up for all categories
        # print(f"result_options: {results_options}")
        # Create options for the results dropdown
        
    
        def find_common_elements(list_of_lists):
            # Convert each sublist to a set
            sets = [set(sublist) for sublist in list_of_lists]
            
            # Find the intersection of all sets
            common_elements = set.intersection(*sets)
            
            # Convert the result back to a list
            return sorted(common_elements)
        
        common_elements = find_common_elements(results_options)
        # print(common_elements)
                
        
        return [{'label': result, 'value': result} for result in common_elements + ["average","best","combined"]]
    else:
        return []

# Define callback to set the value of the results dropdown to the first option when the competition or category changes
@app.callback(
    Output('results-dropdown3', 'value'),
    [Input('competition-dropdown3', 'value'),
     Input('category-dropdown3', 'value')],
    [State('results-dropdown3', 'options')]
)
def set_results_dropdown_value(competition, category, options):
    if options:
        return options[0]['value']
    else:
        return None

# Define callback to update the options of the category dropdown based on the selected competition
@app.callback(
    Output('category-dropdown3', 'options'),
    [Input('competition-dropdown3', 'value')],
    [State('results-store3', 'data')]
)
def update_category_dropdown(competition, database):
    if competition:
        category_options = database['overview'][competition].keys()
        # Create options for the results dropdown
        return [{'label': database['category_acronyms'][category], 'value': category} for category in category_options]
    else:
        return []

# Define callback to set the value of the category dropdown to the first option when the competition changes
@app.callback(
    Output('category-dropdown3', 'value'),
    [Input('competition-dropdown3', 'value')],
    [State('category-dropdown3', 'options')]
)
def set_category_dropdown_value(competition, options):
    if options:
        return options[0]['value']
    else:
        return None

# Progress bar callbacks

# Global variables to track the progress
calculating = False
progress = 0


# Callback to generate tables when the "Calculate" button is clicked
@app.callback(
    [Output('tables-container', 'children'),
    Output('calculate-button', 'style'),
    Output('calculate-button', 'children'),
    Output('alert-container','children')],
    # Output('progress-interval', 'disabled'),
    [Input('calculate-button', 'n_clicks')],
    [State('competition-dropdown3', 'value'),
    State('category-dropdown3', 'value'),
    State('results-dropdown3', 'value'),
    State('xx-input', 'value'),
    State('yy-input', 'value'),
    State('zz-input', 'value'),
    State('top-x-input', 'value')]
    )

def generate_tables(n_clicks, competition, categories, results, xx_value, yy_value, zz_value, num_scenarios):
    #adding progress bar code
    global progress, calculating
    
    #We need to return the calculate button back
    button_style = {'display': 'block', 'margin-top': '10px', 'width': '150px', 'height': '40px', 'background-color': 'green', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'} 
    button_text =  'Calculate'
    
    
    

    tables = []
    if n_clicks:
        #start with progress = 0
        progress = 0
        #change calculating variable to true
        calculating = True
        
        #lets check we''ve selected competition, category and results
        missing = []
        if not(competition):
            missing.append('Competition')
        if not(categories):
            missing.append('Category')
        if not(results):
            missing.append('Results')
        
        #if anything is missing, we cannot calculate
        
        if missing:
            missing_text = ', '.join(missing)
            alert = dbc.Alert(
                "Missing "+missing_text+" selection above, please select and try again",
                color="red",
                dismissable=True,
                is_open=True,
                style={'fontSize': '18px'}  # Make the alert text larger
            )
            
            return dash_table.DataTable(),button_style,button_text,alert
        
        
        
        
        comp_format = [xx_value,yy_value,zz_value]
        team_size = xx_value

        elligible_athletes = []
        for athlete in database:
            if athlete not in exclude_keys:
                #check competition
                if competition in database[athlete].keys():
                    #check category
                    if database[athlete][competition]['category'] in categories:
                        #check if they competed that day
                        if results in database[athlete][competition].keys():
                            #then the athlete is elligible
                            elligible_athletes.append(athlete)

        #Here is where we could add the feature to NOT INCLUDE certain gymnasts
        # names.remove('CARROLL Jordan')
        # names.remove('ALLAIRE Dominic')
        
        all_combos = list(itertools.combinations(elligible_athletes, team_size))

        #let's try
        combo_scores = []
        # start_time = time.monotonic()
        
        #get all combos length for progress calcs
        total_combos = len(all_combos)
        
        
        
        
        #Need to check 2 scenarios: 
        #1: # of athletes vs. team size
        #2: # of combos vs. # of top scenarios selected
        
        #scenario 1 alert
        num_athletes = len(elligible_athletes)
        if num_athletes < xx_value:
            #in this scenario, the team size wont work
            alert = dbc.Alert(
                f"Cannot compute: Elligible Athletes ({num_athletes}) is < team size ({xx_value})",
                color="red",
                dismissable=True,
                is_open=True,
                style={'fontSize': '18px'}  # Make the alert text larger
            )
            
            return dash_table.DataTable(),button_style,button_text,alert
        
        #scenario 2 alert
        if total_combos < num_scenarios:

            alert = dbc.Alert(
                f"Cannot compute: Total Possible Team Score Combinations ({total_combos}) is < Number of Scenarios Selected to be Shown ({num_scenarios})",
                color="red",
                dismissable=True,
                is_open=True,
                style={'fontSize': '18px'}  # Make the alert text larger
            )
            
            return dash_table.DataTable(),button_style,button_text,alert
        
        
        for idx, combo in enumerate(all_combos):
            
            team_score = team_score_calcs(comp_format,combo,database,competition,results=results,print_table=False)
            combo_scores.append(team_score['Team']['AA'])
            
            #update progress bar data
            progress = int((idx + 1) / total_combos * 100)
            # time.sleep(0.1)  # Simulate time-consuming calculations
            
            #collect garbage
            # gc.collect()
            
        # end_time = time.monotonic()
        # time_for_all = timedelta(seconds=end_time - start_time)
        # print(f"Time for all: {time_for_all}")

        #% Try zipping lists and then sorting to rank
        combined = list(zip(list(combo_scores), all_combos))
        #sort it
        combined.sort(key=lambda x:x[0],reverse=True)
        #https://stackoverflow.com/questions/20099669/sort-multidimensional-array-based-on-2nd-element-of-the-subarray

        # #colour coding if we want (TODO)
        # colour_dict = {"scratch":"red",
        #                "dropped":"black",
        #                "counting":"white"}
        
        
        for i in range(num_scenarios):
            # print(f"post-processing: {i+1}/{num_scenarios}")
            # team = combined[0][1]
            
            # new_team_scores = team_score_calcs(comp_format,team,database,print_table=False)
        
            #created table 
            tlas=['FX','PH','SR','VT1','PB','HB','AA']
            team = combined[i][1]
            
            team_scores = team_score_calcs(comp_format,team,database,competition,results=results,print_table=False)
            table = []
            
            # print(f"team_scores: {team_scores}")
            
            for athlete in team:
                new_line = {}
                new_line['Athlete'] = athlete
                for tla in tlas:
                    #choose colour based on count 
                    #new_line.append(team_scores[athlete][tla][0])
                    #new_line.append(team_scores[athlete][tla][1])
                    # new_line.append(colored(team_scores[athlete][tla][0],colour_dict[team_scores[athlete][tla][1]]))
                    
                    # print('team_scores[athlete][tla]')
                    # print(team_scores[athlete][tla])
                    try:
                        new_line[tla]=team_scores[athlete][tla][0]
                        new_line[tla+"_status"]=team_scores[athlete][tla][1]
                    except:
                        new_line[tla]=team_scores[athlete][tla]
                    # new_line.append(colored(team_scores[athlete][tla][1],colour_dict[team_scores[athlete][tla][1]]))
                    
                    # header.append(tla)
                    # header.append("count")
                #We also add their AA scores
                # new_line.append(team_scores[athlete]['AA'])
                
                table.append(new_line)
            #summary line
            summary_line = {} #["Team"]
            summary_line['Athlete'] = 'Team Total'
            for tla in tlas:
                summary_line[tla] = np.round(team_scores['Team'][tla],3)
                if tla != "AA":
                    summary_line[tla+"_status"] = "N/A"
            table.append(summary_line)
            # print('team scores')
            # print(team_scores)
            # print('table')
            # print(table)
            table_data = table
            # table_data = team_score_dummy  # For now, using the same data for all tables
            # Truncate all numerical values to three decimal places
            for row in table_data:
                for key, value in row.items():
                    if isinstance(value, (int, float)):
                        row[key] = "{:.3f}".format(value)
            
            # print(f"table data: {table_data} ")
            
            table = generate_table(table_data)
            tables.append(html.Div([html.H3(f'Team Scenario {i+1} using {results} results and {xx_value}-{yy_value}-{zz_value} competition format: {table_data[-1]["AA"]}'), table]))  # Add a heading for each table
            
            #rest clicks to get calculate button back
            # reset_n_clicks(n_clicks)
        
    progress = 100  # Ensure progress is set to 100% when done
    calculating = False #no longer calculating
    
    #We need to return the calculate button back
    button_style = {'display': 'block', 'margin-top': '10px', 'width': '150px', 'height': '40px', 'background-color': 'green', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'} 
    button_text =  'Calculate'
    return tables,button_style,button_text,"" #, True

#%% Combining 3 Tabs
# app.layout = html.Div(
#     # style={'backgroundColor': '#f0f0f0', 'height': '100vh'},  # Set background color and full height
#     [
#     dcc.Tabs(id='tabs-example', value='tab-1', children=[
#         dcc.Tab(label='Competition Overview', value='tab-1'),
#         dcc.Tab(label='Individual Athlete Analysis', value='tab-2'),
#         dcc.Tab(label='Team Scenarios', value='tab-3'),
#     ]),
#     html.Div(id='tabs-content')
# ])


#%% Combining 3 Tabs

app.layout = html.Div(
    # style={'backgroundColor': '#f0f0f0', 'height': '100vh'},  # Set background color and full height
    children=[
        dcc.Tabs(id='tabs-example', value='tab-1', children=[
            dcc.Tab(label='Competition Overview', value='tab-1'),
            dcc.Tab(label='Individual Athlete Analysis', value='tab-2'),
            # dcc.Tab(label='Team Scenarios', value='tab-3'),
        ]),
        html.Div(id='tabs-content')
    ]
)

#%%
@app.callback(Output('tabs-content', 'children'),
              [Input('tabs-example', 'value')])
def render_content(tab):
    if tab == 'tab-1':
        return overview_layout
    elif tab == 'tab-2':
        return tab2_layout
    elif tab == 'tab-3':
        return tab3_layout

#%% comment out when pusing to github
if __name__ == '__main__':
    app.run_server(debug=True)













