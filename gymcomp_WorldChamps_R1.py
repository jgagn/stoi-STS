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

SERIES = "WCups2025"

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
        table_rows = []
        for i in range(len(df)):
            row_data = df.iloc[i]
            background_color = 'yellow' if row_data['Athlete name'] == selected_athlete else ('white' if i % 2 == 0 else '#e6f2ff') #making it blue if not selected
            table_row = html.Tr(
                [html.Td(row_data[col], style={'background-color': background_color, 'padding': '10px'}) for col in df.columns]
            )
            table_rows.append(table_row)
        
        table = html.Table(

            [html.Tr([html.Th(col, style={'padding': '10px', 'background-color': '#cce7ff'}) for col in df.columns])] +
            # Body
            table_rows,
            style={'border-collapse': 'collapse', 'width': 'auto'}
            
        )
    
    return table

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

    html.H3("How to Use The Competition Overview Tab"),
    html.P("Follow these steps to interact with the data:"),

    html.Ol([
        html.Li("Use the Competition selector to choose a competition from the dropdown list."),
        html.Li("Select one or more categories using the Category selector to filter the results accordingly."),
        html.Li("Choose the type of results you want to see (ex. day 1, day 2, average, best) using the Results selector."),
        html.Li("Use the Apparatus selector to further refine the data by apparatus."),
        html.Li("View the interactive bubble plot and data table below for detailed insights.")
    ]),
    
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    html.H3('Competition Data Selection'),

    dbc.Row([
        dbc.Col([
            html.Div([
                html.Div([
                    html.Div("Competition", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
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
                    html.Div("Category (can select more than 1):", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
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
        
    #add some global stats later
    #     dbc.Col([
    #         html.Div([
    #             html.P("Number of Athletes: 50"),
    #             html.P("Top Score: 98.5"),
    #             html.P("Top D Score: 6.2"),
    #             html.P("Top E Score: 9.1"),
    #         ], style={'paddingLeft': '20px'}) #removed border code, 'borderLeft': '1px solid #ccc'})  # Adjust padding and add a border for separation
    #     ], style={'flex': '0 0 60%'})  # Adjust width as needed
    
    ], style={'display': 'flex', 'alignItems': 'flex-start'}),
    
    
    dcc.Store(id='results-store', data=database),  # Store the database - needed to dynamically change data in dropdown menus
    
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),

    dbc.Container([
        html.H3('Interactive Bubble Plot'),
        
        html.P("Understanding the Interactive Bubble Plot and Data Table:"),
        html.Ol([
            html.Li("The bubble plot visualizes scores with bubbles representing athletes. The x-axis shows the E score, and the y-axis shows the D score."),
            html.Li("The size of the bubble corresponds to the athlete's overall score, and the color intensity represents the score magnitude."),
            html.Li("Hover over a bubble to see detailed information, including the athlete's name, category, and scores."),
            html.Li("Clicking a bubble highlights the corresponding athlete's row in the data table."),
            html.Li("The data table provides a ranked list of athletes based on the selected criteria, with columns for rank, athlete name, category, D score, E score, and total score."),
            html.Li("Rows in the data table are highlighted when corresponding bubbles are clicked, making it easier to cross-reference data between the plot and table."),
            html.Li("Use the toolbar above the bubble plot to save the plot as an image, zoom in or out, and crop specific sections of the plot for a closer view.")
        ]),
        
        # html.Div([
        #     html.Div("Plot Type (Bubble or Histogram)", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
        #     dcc.Dropdown(
        #         id='plot-dropdown',
        #         # value='SR21', #initializing with this value for now - should be dynamic
        #         style=dropdown_style1,
        #         multi=False # Enable multi-select
        #     )
        # ], style={'marginBottom': '10px'}),
        
        # dbc.Switch(
        # id='plot-switch',
        # label='Bubble Plot',
        # value=True,  # True = Bubble, False = Histogram
        # style={'margin-bottom': '10px'}
        #     ),
        
        dbc.RadioItems(
        id='plot-toggle',
        options=[
            {'label': 'Bubble Plot', 'value': 'bubble'},
            {'label': 'Histogram', 'value': 'hist'}
        ],
        value='bubble',
        inline=True
            ),
        
    #     html.Div([
    #     html.Div("Plot Type:", style={'marginRight': '10px', 'verticalAlign': 'middle', 'display': 'inline-block'}),
    #     dbc.RadioItems(
    #         id='plot-toggle',
    #         options=[
    #             {'label': 'Bubble Plot', 'value': 'bubble'},
    #             {'label': 'Histogram', 'value': 'histogram'}
    #         ],
    #         value='bubble',
    #         inline=True,  # makes the buttons side by side
    #         inputStyle={"margin-right": "5px", "margin-left": "15px"},  # spacing between radio circles and labels
    #         labelStyle={"margin-right": "20px"}  # spacing between labels
    #     )
    # ], style={'marginBottom': '10px', 'display': 'flex', 'align-items': 'center'}),
        
        
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='bubble-plot', config={'responsive': True}),
                style={'flex': '0 0 80%'},  # Adjust width as needed
            )
        ], style={'display': 'flex'}),
        
        # Customized horizontal line to separate sections
        html.Hr(style={'borderTop': '3px solid #bbb'}),
        
        html.H3("Data Table"),
        dbc.Row([
            dbc.Col(
                html.Div(id='table-container'),
                style={'flex': '0 0 100%'},  # Adjust width as needed
            )
        ], style={'display': 'flex'})
    ], style={'boxSizing': 'border-box', 'position': 'relative', 'width': '100%', 'height': '0', 'paddingBottom': '60%'}),
    
    
    #bottom note:
    # html.P('for any additional inquiries, please email info@stoianalytics.com')
        
    
])

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
     Input('bubble-plot', 'clickData')]  # Add clickData as input
)
def update_plot_and_table(results, apparatus, categories, competition, clickData):
    # Update bubble plot
    # print(f"plot and table categories: {categories}")
    
    #need to make sure categories is a list, it should  be sometimes isn't
    if not isinstance(categories, list):
        categories = [categories]
    
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
        selected_athlete = clickData['points'][0]['hovertext']
        table = update_table(database, competition, categories, results, apparatus, selected_athlete)
    else:
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
        # competitions = database[athlete]["WCups2025"].keys()
        exclusions = ["category", "average", "best", "combined"]
        competitions = [k for k in database[athlete]["WCups2025"].keys() if k not in exclusions]
        comp_days_date = []
        # i = 0 #temporary date counter
        for comp in competitions:
            #also sketchy, hard coding in competition seroies
            results = [key for key in database[athlete]['WCups2025'].keys() if key not in ["category", "average", "best","combined"]]
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
                comp_labels.append(comp+" ("+day+")")
                score = database[athlete]['WCups2025'][comp][tla]['Score']
                categories.append(database[athlete]['WCups2025']['category'])
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


tab2_layout = html.Div([
    
    html.H3("How to Use The Individual Athlete Analysis Tab"),
    html.P("Follow these steps to interact with the data:"),
    html.Ol([
        html.Li("Select an athlete using the Athlete dropdown to view their scores across different competitions."),
        html.Li("View the interactive subplot below to see the athlete's performance across all apparatus over multiple competitions."),
        html.Li("Click on the toolbar above the plots to save the plot as an image, zoom in or out, and crop specific sections of the plot for a closer view.")
    ]),
    
    #legends
    html.P("Apparatus Legend"),
    create_apparatus_legend(tla_dict),
    html.P("Competition Legend"),
    create_competition_legend(database['competition_acronyms']),
    
    # Customized horizontal line to separate sections
    html.Hr(style={'borderTop': '3px solid #bbb'}),
    
    html.H3('Plot Athlete Scores Across Competitions'),
    
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
    
    
    html.P("Follow these steps to use the Score Breakdown Plot:"),
    html.Ol([
        html.Li("Use the Competition and Results dropdowns to filter the score breakdown by specific competitions and results."),
        html.Li("Hover over the bars in the score breakdown plot to see detailed D and E scores for each apparatus."),
        html.Li("Click on the toolbar above the plots to save the plot as an image, zoom in or out, and crop specific sections of the plot for a closer view.")
    ]),
    
    
    html.Div([
        html.Div("Competition", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
        dcc.Dropdown(
            id='competition-dropdown2',
            # options=[{'label': database['competition_acronyms'][comp], 'value': comp} for comp in database['overview'].keys()],
            value=list(next(iter(database.values())).keys())[0],
            multi=True, #New
            style=dropdown_style2
        ),
        
        # html.Div("Results (can select more than 1):", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
        # dcc.Dropdown(
        #     id='results-dropdown2',
        #     # options=[{'label': day, 'value': day} for day in database[next(iter(database))].keys()],
        #     value=['day1','day2'],  # Default value
        #     multi=True,  # Allow multi-select
        #     style=dropdown_style2
        # )
    ]),
    # dcc.Store(id='results-store2', data=database),  # Store the database - needed to dynamically change data in dropdown menus
    dcc.Graph(id='score-graph'), #, style={'width': '1000px', 'height': '400px'}),
    
])

#SINGLE DROPDOWN CALLBACKS

# Define a single callback to update both competition and results dropdowns
# @app.callback(
#     [Output('competition-dropdown2', 'options'),
#      Output('competition-dropdown2', 'value'),
#      Output('results-dropdown2', 'options'),
#      Output('results-dropdown2', 'value')],
#     [Input('athlete-dropdown2', 'value'),
#      Input('competition-dropdown2', 'value')],
#     [State('results-store2', 'data')]
# )

# def update_dropdowns(athlete, competition, database):
#     ctx = callback_context
#     triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
#     #super sketchy function that im hardcoding stuff in now
    
#     if triggered_id == 'athlete-dropdown2':
#         if athlete:
            
#             exclusions = ["category", "average", "best", "combined"]
#             competitions = [k for k in database[athlete]["WCups2025"].keys() if k not in exclusions]
#             # competitions = list(database[athlete]["WCups2025"].keys())
#             comp_options = [{'label': database['competition_acronyms'][comp], 'value': comp} for comp in competitions]
            
#             return comp_options, None, [], None
#         else:
#             return [], None, [], None

#     elif triggered_id == 'competition-dropdown2':
#         if athlete and competition:
#             #Super sketchy here i am hardcoding competition and category
#             #TODO
#             results_options = [day for day in database[athlete]["WCups2025"][competition].keys() if day != "category"]
#             return dash.no_update, dash.no_update, [{'label': result, 'value': result} for result in results_options], None
#         else:
#             return dash.no_update, dash.no_update, [], None

#     return [], None, [], None
#PLOT 1 CALLBACKS

@app.callback(
    [Output('competition-dropdown2', 'options'),
     Output('competition-dropdown2', 'value')],
    [Input('athlete-dropdown2', 'value')]
)
def update_competition_dropdown(athlete):
    if athlete:
        exclusions = ["category", "average", "best", "combined"]
        competitions = [k for k in database[athlete]["WCups2025"].keys() if k not in exclusions]
        comp_options = [{'label': database['competition_acronyms'][comp], 'value': comp} for comp in competitions]
        return comp_options, None
    else:
        return [], None


# @app.callback(
#     Output('score-graph', 'figure'),
#     [Input('athlete-dropdown2', 'value'),
#      Input('competition-dropdown2', 'value'),
#      Input('results-dropdown2', 'value'),
#      ]
# )
# def update_score_graph(athlete, competition, results):
#     traces = []
#     max_score = 0

#     #lets check to see if we have everythin selected
#     if athlete and competition and results:
        
#         #lets make sure it is a list if its not make it one
#         if not isinstance(results, list):
#             results = [results]
        
#         #width and offset will be based on number of days selected
#         n_days = len(results)
#         # print(f"n_days: {n_days}")
        
#         # print(f"width: {barplot_width(n_days)}")
#         width = barplot_width(n_days)
        
#         # Define an offset multiplier for each day
#         #starting with negative offset so we are always around zero
#         offset_multiplier = -width*(n_days-1)/2
        
#         for i,result in enumerate(results):
#             # athlete = database[athlete][competition]
#             d_scores = []
#             e_scores = []
#             plot_apparatus = ['FX','PH','SR','VT1','VT2','PB','HB']
            
#             for app in plot_apparatus:
#                 d_scores.append(database[athlete][competition][result][app]['D'])
#                 e_scores.append(database[athlete][competition][result][app]['E'])
#                 # max_score = 16 #max(max_score, max(database[athlete][competition][result][app]['Score'])) #+athlete[day][app]['E'])) #, athlete[day][app]['E']))
#                 score = database[athlete][competition][result][app]['Score']
#                 if score > max_score:
#                     max_score = score
#             # print(barplot_colours['D'][day])
            
#             # Create stacked bar trace for D and E scores
#             stacked_trace_d = go.Bar(
#                 x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
#                 y=d_scores,
#                 name=f'D score ({result})',
#                 # hoverinfo='y+name',
#                 hovertext=[f'{d:.3f}' for d in d_scores],
#                 hoverinfo='text+name',  # Use custom hover text and show trace name
                
#                 marker_color=barplot_colours['D'][i],  # Set color for D scores
#                 # marker_pattern='cross',
#                 # marker=dict(pattern='+', pattern_fgcolor='black'),
#                 # marker_pattern_fgcolor=barplot_colours['E'][day],
#                 offsetgroup=result,  # Group by day
#                 legendgroup=result,  # Group by day
#                 width = width,
#             )
            
            
#             stacked_trace_e = go.Bar(
#                 x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
#                 y=e_scores,
#                 name=f'E score ({result})',
#                 #custom hover text
#                 # hoverinfo='y+name',
#                 hovertext=[f'{e:.3f}' for e in e_scores],
#                 hoverinfo='text+name',  # Use custom hover text and show trace name
                
#                 marker_color=barplot_colours['E'][i],  # Set color for E scores
#                 offsetgroup=result,  # Group by day
#                 legendgroup=result,  # Group by day
#                 base=d_scores,  # Offset by D scores
#                 width = width,
#                 # Adding text above the bar plot for the whole score, truncated to 3 decimal places
#                 text=[f'{d + e:.3f}' for d, e in zip(d_scores, e_scores)],
#                 textposition='outside'
#             )
            
#             traces.append(stacked_trace_d)
#             traces.append(stacked_trace_e)
            
            
#             # Increment the offset multiplier for the next day
#             offset_multiplier += width # Adjust the multiplier as needed to prevent overlapping bars
        
#         layout = go.Layout(
#         title=f'Score Breakdown for {athlete} at {database["competition_acronyms"][competition]}',
#         xaxis={'title': 'Apparatus'},
#         yaxis={'title': 'Score', 'range': [0, max_score * 1.1]},
#         barmode='relative',  # Relative bars for stacked and grouped
#         # width=1000,
#         height=400
#         )
    
#         # Set x-axis tick labels to be the apparatus names
#         layout['xaxis']['tickvals'] = list(range(len(plot_apparatus)))
#         layout['xaxis']['ticktext'] = plot_apparatus
#         # print(f"plot app: {plot_apparatus}")
#     else:
#         #if we havent selected valid inputs yet, return blank
#         traces = [go.Bar()]
#         layout = go.Layout()
        
#     return {'data': traces, 'layout': layout}


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
            plot_apparatus = ['FX','PH','SR','VT1','VT2','PB','HB']
            
            for app in plot_apparatus:
                d_scores.append(database[athlete][SERIES][comp][app]['D'])
                e_scores.append(database[athlete][SERIES][comp][app]['E'])
                # max_score = 16 #max(max_score, max(database[athlete][competition][result][app]['Score'])) #+athlete[day][app]['E'])) #, athlete[day][app]['E']))
                score = database[athlete][SERIES][comp][app]['Score']
                if score > max_score:
                    max_score = score
            # print(barplot_colours['D'][day])
            
            # Create stacked bar trace for D and E scores
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
                base=d_scores,  # Offset by D scores
                width = width,
                # Adding text above the bar plot for the whole score, truncated to 3 decimal places
                text=[f'{d + e:.3f}' for d, e in zip(d_scores, e_scores)],
                textposition='outside'
            )
            
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
        height=400
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
            html.Div("Category (can select more than 1):", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
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
            dcc.Tab(label='Team Scenarios', value='tab-3'),
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













