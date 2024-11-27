#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 13:38:51 2024

@author: joelgagnon
"""

#%% gymcomp R1

#2024-03-26
#starting fresh -> plotly dash app

# 3 tabs with 3 key features
# 1: Competition Overview
# 2: Individual Athlete Analysis
# 3: Team Scenarios


#%% Imports

import dash
from dash import dcc, html, dash_table
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

#dash authentication
# import dash_auth # pip install dash-auth==2.0.0. <- add this to requirements.txt

# Import the print function
from builtins import print

#import the team scenarios calc
from team_scenario_calcs import team_score_calcs
#%% Import Data 
#use absolute path

# Get the absolute path to the directory containing the main app file
base_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the absolute path to the file
file_path = os.path.join(base_dir, "test_data/EliteCanada2024/jrdatabase")


with open(file_path, 'rb') as f:
    database = pickle.load(f)

# print("Database loaded successfully.")

#%%  Function to calculate the color based on the score
def get_color(score, max_score):
    if math.isnan(score):
        return 'black'  # or any other default color
    else:
        # Calculate the color based on the score and max score
        color_value = score / max_score
        return color_value

#%% Setup App, Title, Authentication
app = dash.Dash(__name__, suppress_callback_exceptions=True) #, external_stylesheets=[dbc.themes.MORPH])

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
###################################
#%% Tab 1: Competition Overview ###
###################################
# Function to calculate the color based on the score
def get_color(score, max_score):
    if math.isnan(score):
        return 'black'  # or any other default color
    else:
        # Calculate the color based on the score and max score
        color_value = score / max_score
        return color_value

# Function to update the bubble plot
def update_bubble_plot(day, apparatus):
    data = {'x': [], 'y': [], 'size': [], 'name': [], 'score': [], 'color': []}
    max_score = max([stats['Score'] for values in database.values() if day in values for app, stats in values[day].items() if app == apparatus])

    exp = 3  # Adjust this as needed

    for name, values in database.items():
        if day in values:
            for app, stats in values[day].items():
                if app == apparatus:
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
                    
                    # Make it zero if it's nan
                    if math.isnan(stats['Score']):
                        size = 0.0
                        color = 0.0
                    else:
                        size = stats['Score']
                        color = stats['Score']
                        
                    data['color'].append(get_color(color ** exp, max_score ** exp))
                        
                    size_exp = 1.5
                    if apparatus == "AA":
                        data['size'].append((size / 6) ** size_exp)
                    else:
                        data['size'].append(size ** size_exp)
    return data

def update_table(day, apparatus, selected_athlete=None):
    # Filter the database based on selected day and apparatus
    filtered_data = {name: stats for name, values in database.items() if day in values for app, stats in values[day].items() if app == apparatus}
    
    # Create DataFrame from filtered data
    df = pd.DataFrame.from_dict(filtered_data, orient='index')
    
    # Sort DataFrame by Score in descending order (if tie, sort by E score for now)
    df = df.sort_values(by=['Score', 'E'], ascending=[False, False])
    
    # Reset index to include Athlete name as a column
    df = df.reset_index().rename(columns={'index': 'Athlete name'})
    
    # Truncate score values to 3 decimal points (do not round)
    df['D score'] = df['D'].map('{:.3f}'.format)
    df['E score'] = df['E'].map('{:.3f}'.format)
    df['Score'] = df['Score'].map('{:.3f}'.format)
    
    # Add rank column
    df['Rank'] = df.index + 1
    
    # Reorder columns
    df = df[['Rank', 'Athlete name', 'D score', 'E score', 'Score']]
    
    # Generate HTML table with highlighted row if a selected athlete is provided
    table_rows = []
    for i in range(len(df)):
        row_data = df.iloc[i]
        background_color = 'yellow' if row_data['Athlete name'] == selected_athlete else 'white'
        table_row = html.Tr([html.Td(row_data[col], style={'background-color': background_color}) for col in df.columns])
        table_rows.append(table_row)
    
    table = html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df.columns])] +
        # Body
        table_rows
    )
    
    return table



#I want to make the drop down selectors take up less width
dropdown_style = {'width': '30%'}  # Adjust the width as needed

# Define layout of the app
overview_layout = html.Div([
    html.H3('Competition Overview'),
    dbc.Row([
        dbc.Col([
            html.Div("Competition Day:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
            dcc.Dropdown(
                id='day-dropdown',
                options=[{'label': day, 'value': day} for day in next(iter(database.values())).keys()],
                value=list(next(iter(database.values())).keys())[0],
                style=dropdown_style
            ),
        ], width=6),
        dbc.Col([
            html.Div("Apparatus:", style={'marginRight': '10px', 'verticalAlign': 'middle'}),
            dcc.Dropdown(
                id='apparatus-dropdown',
                options=[{'label': app, 'value': app} for app in ["FX", "PH", "SR", "VT", "PB", "HB", "AA"]],
                value='AA',
                style=dropdown_style
            ),
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Graph(id='bubble-plot'),
            width=6
        ),
        dbc.Col(
            html.Div(id='table-container'),
            width=6
        )
    ])
])


# Define callback to update the bubble plot and table based on selected options
# Define callback to update the bubble plot and table based on selected options
@app.callback(
    [Output('bubble-plot', 'figure'),
     Output('table-container', 'children')],
    [Input('day-dropdown', 'value'),
     Input('apparatus-dropdown', 'value'),
     Input('bubble-plot', 'clickData')]  # Add clickData as input
)
def update_plot_and_table(day, apparatus, clickData):
    # Update bubble plot
    data = update_bubble_plot(day, apparatus)
    fig = px.scatter(data, x='x', y='y', color='color', size='size', hover_name='name',
                     color_continuous_scale='Viridis', opacity=0.6, hover_data={'name': True, 'x': False, 'y': False, 'size': False})
    fig.update_layout(title="Interactive Chart", 
                      xaxis_title="E score", 
                      yaxis_title="D score", 
                      autosize=True,
                      margin=dict(l=40, r=40, t=40, b=40),
                      width=1000, #play with this value until you like it
                      height=600,
                      )
    fig.update_traces(text=data['score'], textposition='top center')  

    # Customize hover template
    hover_template = ("<b>%{hovertext}</b><br>" +
                      "D score: %{y:.3f}<br>" +
                      "E score: %{x:.3f}<br>" +
                      "Score: %{text:.3f}")
    fig.update_traces(hovertemplate=hover_template)
    
    # Update color bar legend
    fig.update_coloraxes(colorbar_title="Score")
    
    # Map color values to score values for color bar tick labels
    color_values = np.linspace(0, 1, 11)  
    max_score = max(data['score'])
    score_values = [value * max_score for value in color_values]  
    
    # Update color bar tick labels
    fig.update_coloraxes(colorbar_tickvals=color_values, colorbar_ticktext=[f"{score:.3f}" for score in score_values])
    
    # If a point is clicked, highlight the corresponding row in the table
    if clickData:
        selected_athlete = clickData['points'][0]['hovertext']
        table = update_table(day, apparatus, selected_athlete)
    else:
        table = update_table(day, apparatus)
    
    return fig, table


########################################
#%% Tab 2: Individual Athlete Analysis #
########################################

#colour dictionary
barplot_colours = {'D':
                       {'day1':'blue',
                       'day2':'green',
                       'average':'orange',
                       'best':'magenta',
                        },
                   'E':
                       {'day1':'#ADD8E6',
                       'day2':'#90EE90',
                       'average':'#FFD700',
                       'best':'#FFB6C1',
                        },
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
    else:
        width=0.0
    return width

# Define layout for the second tab with dropdowns and bar graph
tab2_layout = html.Div([
    html.H3('Individual Athlete Analysis'),
    html.Div([
        dcc.Dropdown(
            id='athlete-dropdown',
            options=[{'label': athlete, 'value': athlete} for athlete in database.keys()],
            value=next(iter(database)),  # Default value
            multi=False,  # Single select
            style={'width': '50%'}
        ),
        dcc.Dropdown(
            id='day-dropdown',
            options=[{'label': day, 'value': day} for day in database[next(iter(database))].keys()],
            value=['day1','day2'],  # Default value
            multi=True,  # Allow multi-select
            style={'width': '50%'}
        )
    ]),
    dcc.Graph(id='score-graph', style={'width': '1000px', 'height': '600px'})
])

@app.callback(
    Output('score-graph', 'figure'),
    [Input('athlete-dropdown', 'value'),
     Input('day-dropdown', 'value')]
)
def update_score_graph(selected_athlete, selected_days):
    traces = []
    max_score = 0
    
    
    
    #width and offset will be based on number of days selected
    n_days = len(selected_days)
    # print(f"n_days: {n_days}")
    
    # print(f"width: {barplot_width(n_days)}")
    width = barplot_width(n_days)
    
    # Define an offset multiplier for each day
    #starting with negative offset so we are always around zero
    offset_multiplier = -width*(n_days-1)/2
    
    for day in selected_days:
        athlete = database[selected_athlete]
        d_scores = []
        e_scores = []
        plot_apparatus = ['FX','PH','SR','VT','PB','HB']
        
        for app in plot_apparatus:
            d_scores.append(athlete[day][app]['D'])
            e_scores.append(athlete[day][app]['E'])
            max_score = 16 #max(max_score, max(athlete[day][app]['Score'])) #+athlete[day][app]['E'])) #, athlete[day][app]['E']))
        
        # print(barplot_colours['D'][day])
        
        # Create stacked bar trace for D and E scores
        stacked_trace_d = go.Bar(
            x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
            y=d_scores,
            name=f'{day} - D',
            hoverinfo='y+name',
            
            marker_color=barplot_colours['D'][day],  # Set color for D scores
            # marker_pattern='cross',
            # marker=dict(pattern='+', pattern_fgcolor='black'),
            # marker_pattern_fgcolor=barplot_colours['E'][day],
            offsetgroup=day,  # Group by day
            legendgroup=day,  # Group by day
            width = width,
        )
        
        
        stacked_trace_e = go.Bar(
            x=[i + offset_multiplier for i in range(len(plot_apparatus))],  # Adjust x-location based on offset_multiplier
            y=e_scores,
            name=f'{day} - E',
            hoverinfo='y+name',
            marker_color=barplot_colours['E'][day],  # Set color for E scores
            offsetgroup=day,  # Group by day
            legendgroup=day,  # Group by day
            base=d_scores,  # Offset by D scores
            width = width,
        )
        
        traces.append(stacked_trace_d)
        traces.append(stacked_trace_e)
        
        # Increment the offset multiplier for the next day
        offset_multiplier += width # Adjust the multiplier as needed to prevent overlapping bars
        
    layout = go.Layout(
    title=f'Score Breakdown for {selected_athlete}',
    xaxis={'title': 'Apparatus'},
    yaxis={'title': 'Score', 'range': [0, max_score * 1.1]},
    barmode='relative',  # Relative bars for stacked and grouped
    width=1000,
    height=600
    )

    # Set x-axis tick labels to be the apparatus names
    layout['xaxis']['tickvals'] = list(range(len(plot_apparatus)))
    layout['xaxis']['ticktext'] = plot_apparatus
    # print(f"plot app: {plot_apparatus}")
    return {'data': traces, 'layout': layout}

######################
#%% Team Scenarios ###
######################

# Sample data for demonstration
team_score_dummy = [
    {'Athlete': 'VANOUNOU Liam', 'FX': 12.475, 'PH': 12.025, 'SR': 12.125, 'VT': 12.900500000000001, 'PB': 12.45, 'HB': 11.8, 'Total': 73.7755},
    {'Athlete': 'GONZALEZ Aiden', 'FX': 12.725, 'PH': 11.625, 'SR': 11.8, 'VT': 12.466999999999999, 'PB': 11.274999999999999, 'HB': 12.925, 'Total': 72.81700000000001},
    {'Athlete': 'HUBER Evan', 'FX': 12.725, 'PH': 10.4, 'SR': 12.4, 'VT': 13.767, 'PB': 12.425, 'HB': 12.075, 'Total': 73.792},
    {'Athlete': 'MADORE Raphael', 'FX': 13.075, 'PH': 10.1, 'SR': 12.524999999999999, 'VT': 13.9505, 'PB': 12.625, 'HB': 11.875, 'Total': 74.1505},
    {'Athlete': 'CARROLL Jordan', 'FX': 0.0, 'PH': 13.625, 'SR': 0.0, 'VT': 0.0, 'PB': 0.0, 'HB': 0.0, 'Total': 13.625},
    {'Athlete': 'Team', 'FX': 38.525, 'PH': 37.275, 'SR': 37.05, 'VT': 40.618, 'PB': 37.5, 'HB': 36.875, 'Total': 227.843}
]


# Header for the table
header = ['Athlete', 'FX', 'PH', 'SR', 'VT', 'PB', 'HB', 'AA']

def generate_table(data):
    return dash_table.DataTable(
        columns=[{'name': i, 'id': i} for i in header],
        data=data,
        style_cell={'textAlign': 'center', 'whiteSpace': 'normal', 'height': 'auto'},  # Ensure text wraps within cells
        style_table={'overflowX': 'auto'},  # Enable horizontal scroll if content overflows
    )

tab3_layout = html.Div([
    html.Label('Results:'),
    dcc.Dropdown(
        id='results-dropdown',
        options=[
            {'label': 'Day 1', 'value': 'day1'},
            {'label': 'Day 2', 'value': 'day2'},
            {'label': 'Average', 'value': 'average'},
            {'label': 'Best', 'value': 'best'}
        ],
        value='day1',
        style={'width': '200px'}  # Adjust width here
    ),

    html.Label('Competition Format:'),
    html.Div([
        dcc.Input(id='xx-input', type='number', min=1, max=15, value=5, style={'width': '50px', 'fontSize': '16px'}),
        html.Label('-', style={'padding': '0 5px'}),  # Added label with padding
        dcc.Input(id='yy-input', type='number', min=1, max=6, value=4, style={'width': '50px',  'fontSize': '16px'}),
        html.Label('-', style={'padding': '0 5px'}),  # Added label with padding
        dcc.Input(id='zz-input', type='number', min=1, max=5, value=3, style={'width': '50px', 'fontSize': '16px'}),
    ]),
    
    html.Label('Show Top', style={'margin-top': '10px'}),  # Added label for the top X team scenarios
    dcc.Input(id='top-x-input', type='number', min=1, max=20, value=5, style={'width': '50px', 'fontSize': '16px'}),  # Added input box for X
    html.Label('team scenarios', style={'margin-left': '5px', 'margin-top': '10px'}),  # Added label for team scenario
    
    
    # html.Div(id="buttons-container", children=[
    #     html.Button('Calculate', id='calculate-button', n_clicks=0, style={'display': 'block', 'width': '150px', 'height': '40px', 'background-color': 'green', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'}),
    #     html.Button('Calculating...', id='loading-button', disabled=True, style={'display': 'none', 'width': '150px', 'height': '40px', 'background-color': 'gray', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'}),
    # ]),
    
    html.Button('Calculate', id='calculate-button', n_clicks=0, style={'display': 'block', 'margin-top': '10px', 'width': '150px', 'height': '40px', 'background-color': 'green', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'}),
    
    # # Loading button widget
    # dcc.Loading(
    #     id="loading-calculate",
    #     type="default",
    #     children=[
    #         html.Button('Calculating...', id='loading-button', disabled=True, style={'display': 'block', 'margin-top': '10px', 'width': '150px', 'height': '40px', 'background-color': 'gray', 'color': 'white', 'border': 'none', 'border-radius': '5px', 'fontSize': '20px'}),
    #         html.Div(id="loading-output-calculate")
    #     ]
    # ),
    
    # html.Button('Calculate', id='calculate-button', n_clicks=0, style={
    #     'display': 'block',
    #     'margin-top': '10px',
    #     'width': '150px',
    #     'height': '40px',
    #     'background-color': 'green',
    #     'color': 'white',
    #     'border': 'none',
    #     'border-radius': '5px',
    #     'fontSize': '20px',
    #     'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)',  # Add box shadow effect
    # }),
    
    # Placeholder for tables that will be updated based on filters
    html.Div(id='tables-container')
])

# Callback to switch between Calculate and Calculating buttons
# @app.callback(
#     Output('calculate-button', 'style'),
#     Output('loading-button', 'style'),
#     Input('calculate-button', 'n_clicks'),
#     prevent_initial_call=True
# )
# def toggle_buttons(n_clicks):
#     if n_clicks % 2 == 1:
#         return {'display': 'none'}, {'display': 'block'}
#     else:
#         return {'display': 'block'}, {'display': 'none'}

# @app.callback(
#     Output('calculate-button', 'n_clicks'),
#     Input('calculate-button', 'n_clicks'),
#     prevent_initial_call=True
# )
# def reset_n_clicks(n_clicks):
#     return 0

# Callback to generate tables when the "Calculate" button is clicked
@app.callback(
    Output('tables-container', 'children'),
    [Input('calculate-button', 'n_clicks')],
    [State('results-dropdown', 'value'),
      State('xx-input', 'value'),
      State('yy-input', 'value'),
      State('zz-input', 'value'),
      State('top-x-input', 'value')]
    )

def generate_tables(n_clicks, results_value, xx_value, yy_value, zz_value, num_scenarios):

    tables = []
    if n_clicks:
        
        #Here is where we will actually do the team score calculations!
        
        results_value = dash.callback_context.states['results-dropdown.value']
        xx_value = dash.callback_context.states['xx-input.value']
        yy_value = dash.callback_context.states['yy-input.value']
        zz_value = dash.callback_context.states['zz-input.value']
        
        
        
        comp_format = [xx_value,yy_value,zz_value]
        team_size = xx_value
        #get names
        names = []
        for name in database:
            names.append(name)

        #Here is where we could add the feature to NOT INCLUDE certain gymnasts
        # names.remove('CARROLL Jordan')
        # names.remove('ALLAIRE Dominic')
        
        all_combos = list(itertools.combinations(names, team_size))

        #let's try
        combo_scores = []
        # start_time = time.monotonic()
        for combo in all_combos:
            team_score = team_score_calcs(comp_format,combo,database,results=results_value,print_table=False)
            combo_scores.append(team_score['Team']['AA'])
        # end_time = time.monotonic()
        # time_for_all = timedelta(seconds=end_time - start_time)
        # print(f"Time for all: {time_for_all}")

        #% Try zipping lists and then sorting to rank
        combined = list(zip(list(combo_scores), all_combos))
        #sort it
        combined.sort(key=lambda x:x[0],reverse=True)
        #https://stackoverflow.com/questions/20099669/sort-multidimensional-array-based-on-2nd-element-of-the-subarray

        #colour coding if we want (TODO)
        colour_dict = {"scratch":"red",
                       "dropped":"black",
                       "counting":"white"}
        
        for i in range(num_scenarios):
            
            # team = combined[0][1]
            
            # new_team_scores = team_score_calcs(comp_format,team,database,print_table=False)
        
            #created table 
            tlas=['FX','PH','SR','VT','PB','HB','AA']
            team = combined[i][1]
            team_scores = team_score_calcs(comp_format,team,database,results=results_value,print_table=False)
            table = []
            
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
            
            table = generate_table(table_data)
            tables.append(html.Div([html.H3(f'Team Scenario {i+1} using {results_value} results and {xx_value}-{yy_value}-{zz_value} competition format: {table_data[-1]["AA"]}'), table]))  # Add a heading for each table
            
            #rest clicks to get calculate button back
            # reset_n_clicks(n_clicks)

    return tables

#%% Combining 3 Tabs
app.layout = html.Div([
    dcc.Tabs(id='tabs-example', value='tab-1', children=[
        dcc.Tab(label='Competition Overview', value='tab-1'),
        dcc.Tab(label='Individual Athlete Analysis', value='tab-2'),
        dcc.Tab(label='Team Scenarios', value='tab-3'),
    ]),
    html.Div(id='tabs-content')
])

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














