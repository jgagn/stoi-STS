#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 24 15:23:04 2024

@author: joelgagnon
"""

#%% Description

# New file to create the athlete database from multiple csv files

#%% Import Libraries

import os
import pandas as pd
import numpy as np
import pickle
import chardet #to detect character encoding - making sure accents and such are saved properly in names
import math

#%% Setup files to import

# competitions = ["COTTBUS","DOHA","OSIJEK","BAKU","CAIRO","ANTALYA"]
competitions = ["JAKARTA"]
# competitions = ["COTTBUS"]

#%% Acronyms
competition_series = ["WorldChamps2025"]
categories = ["SR"]
# days = ["QF","EF"]
days = ["QF","AA"]
series_acronyms = {
                    # "2025 World Cup Series": "2025 World Cup Series"
                    # "EF":"Event Finals",
                    # "QF":"Qualifications",
                    # "Cottbus": "Cottbus"
                    "WorldChamps2025": "World Championships 2025"
                    }

competition_acronyms = {
                    "JAKARTA-QF":"Qualifcations",
                    "JAKARTA-AA":"All Around Finals",
                    # "COTTBUS-EF":"Cottbus (EF)",
                    # "BAKU-QF":"Baku (QF)",
                    # "BAKU-EF":"Baku (EF)",
                    # "DOHA-QF":"Doha (QF)",
                    # "DOHA-EF":"Doha (EF)",
                    # "ANTALYA-QF":"Antalya (QF)",
                    # "ANTALYA-EF":"Antalya (EF)",
                    # "CAIRO-QF":"Cairo (QF)",
                    # "CAIRO-EF":"Cairo (EF)",
                    # "OSIJEK-QF":"Osijek (QF)",
                    # "OSIJEK-EF":"Osijek (EF)",
                    }


category_acronyms = {"SR":"Senior",
                     }

series_dates = {
                    "WorldChamps2025": "2025-10-20"}

competition_dates = {
                    # "WCups2025": "2025-02-21",
                    "JAKARTA-QF":"2025-10-20",
                    "JAKARTA-AA":"2025-10-22",
                    # "COTTBUS-EF":"2025-02-23",
                    # "BAKU-QF":"2025-03-06",
                    # "BAKU-EF":"2025-03-08",
                    # "DOHA-QF":"2025-03-16",
                    # "DOHA-EF":"2025-03-18",
                    # "ANTALYA-QF":"2025-03-20",
                    # "ANTALYA-EF":"2025-03-22",
                    # "CAIRO-QF":"2025-03-25",
                    # "CAIRO-EF":"2025-03-26",
                    # "OSIJEK-QF":"2025-04-12",
                    # "OSIJEK-EF":"2025-04-13",
                    # "QF": "2025-02-21",
                    # "EF": "2025-02-23",
                    # "TF": "2024-07-02",
                    # "AA": "2024-07-03",
                    # "EF": "2024-07-04",
                        }



#%% Rename column headers
# the format is a bit silly, where there are two levels of headers
# the key is that the data goes D score, Score and Rank
order = ["D","E","ND","Bonus","Score"]
Ename = "E"

columns = ["D Score","E Score","Penalty","Bonus","Final Score"]


# apparatus = ["Floor","Pommel Horse","Rings","Vault","Parallel Bars","High Bar","AllAround"]

#create a dictionary where the csv appartus names are keys to desired apparatus abbreviation values
#two-letter acronyms we want to use No AA in WCs leaving in for now!
tlas = ["FX","PH","SR","VT1","VT2","PB","HB"] #,"AA"]
tlas = ["FX","PH","SR","VT1","PB","HB"] #,"AA"]
comp_tlas = ["FX","PH","SR","VT1","PB","HB"]

# abbrev_dict = {apparatus[0]:tlas[0],
#                apparatus[1]:tlas[1],
#                apparatus[2]:tlas[2],
#                apparatus[3]:tlas[3],
#                apparatus[4]:tlas[4],
#                apparatus[5]:tlas[5],
#                apparatus[6]:tlas[6],
#                }
new_columns = []
i = 0

#%% Do some  prep work to figure out which categories and competitiond days occured for all competitions
comp_overview = {}

#extract unique competitions
# competitions = database['Competition'].unique()

#for each competition, extract categories
for series in competition_series:
    comp_overview[series] = {}
    for category in categories:
        comp_overview[series][category] = {}
        for comp in competitions:
            comp_overview[series][category][comp] = []
            for day in days:
                comp_overview[series][category][comp].append(day) #+"-"+day)
        
        
#%% Organize into athlete specific database


athlete_database = {}

#get all athlete names
# Extract unique values from the column

#lets get all athlete names...

dfs = []
for comp in competitions:
    # Detect the encoding
    for day in days:
        for tla in comp_tlas:
            with open(comp+"_csv/"+comp+"_"+day+"_"+tla+".csv", 'rb') as f:
                result = chardet.detect(f.read())
        
            # Extract the detected encoding
            encoding = result['encoding']
            print(f"{comp}-{tla}-{day} - Detected encoding: {encoding}")
            
            #overriding to utf-8
            encoding = "utf-8"
            # Read the CSV file with the detected encoding
            database = pd.read_csv(comp+"_csv/"+comp+"_"+day+"_"+tla+".csv", encoding=encoding)
            
            #add the competition, and apparatus, category
            database['apparatus'] = tla
            database['Competition'] = comp
            database['Results'] = day
            database['Category'] = "SR"
            
            #rename 
            if tla != "VT":
                for i,score in enumerate(order):
                    database.rename(columns={columns[i]: tla+"_"+score}, inplace=True)

            dfs.append(database)


database = pd.concat(dfs, ignore_index=True)
# Create new "Athlete" column by merging last and first names

database['Athlete'] = database['Last Name'] + ' ' + database['First Name']
athletes = database['Athlete'].unique()

#remove any non strings - should only be in my incompelte test data
athletes = [athlete for athlete in athletes if isinstance(athlete, str)]


#%%$ lets add the comp overivew data and competition data to the athlete_database

athlete_database['overview'] = comp_overview

#add acronym data here
athlete_database['competition_acronyms'] = competition_acronyms
athlete_database['series_acronyms'] = series_acronyms

athlete_database['category_acronyms'] = category_acronyms
#and date data
athlete_database['competition_dates'] = competition_dates
athlete_database['series_dates'] = series_dates

for athlete in athletes:
    #create an dictionary entry for the athlete in the athlete_database
    # print(f"{athlete}")
    athlete_database[athlete] = {}
    #Lets start by going through each competition
    for series in competition_series:
        for comp in comp_overview[series]['SR']:
            #let's see if the athlete competed in that comp
            
            # Filter the DataFrame
            matching_entries = database[(database['Athlete'] == athlete) & (database['Competition'] == comp)]
            # Check if there is any matching entry
            
            # print(f"comp: {comp}")
            if not matching_entries.empty:
                
                
                #1. create a dictionary entry for this competition serires
                athlete_database[athlete][series] = {}
                
                
                #2. let's obtain what category they were in for this competition
                filtered_df = database[(database['Athlete'] == athlete) & (database['Competition'] == comp)]
                category = filtered_df.iloc[0]['Category']
                
                #new - get country code
                country = filtered_df.iloc[0]['Country']
                
                #3. append the category they are in for this competition -> important as athletes may change categories
                athlete_database[athlete][series]['category'] = category
                
                #new - add country code
                athlete_database[athlete][series]['country'] = country
                
                #4. Get what days they would've competed at this comp based on their category
                days = comp_overview[series][category][comp]
                
    
                #5. Loop through these competition days, and append all data to athlete_database if they exist
                for day in days:
                    #check if it exists
                    filtered_df = database[(database['Athlete'] == athlete) & (database['Competition'] == comp) & (database['Results'] == day)]
                    #if its not empty, lets append the data
                    if not filtered_df.empty:
                        # print(f"{athlete} competeted {day} at {comp}")
                        athlete_database[athlete][series][comp+"-"+day] = {}
                        # print(filtered_df)
                        #Now append all data
                        for tla in tlas:
                            #query the dataframe to obtain all data
                            athlete_database[athlete][series][comp+"-"+day][tla] = {}
                            
                            #the way I am creating the inital database now
                            #means that each apparatus is in its own row
                            #i need to filter by apparatus column also in this case
                            filtered_df = database[(database['Athlete'] == athlete) & (database['Competition'] == comp) & (database['Results'] == day) & (database['apparatus'] == tla)]
                            
                            for value in order:
    
                                val = filtered_df[f'{tla}_{value}']
                                
                                #change to zero if its nan
                                
                                try:
                                    athlete_database[athlete][series][comp+"-"+day][tla][value] = float(val.iloc[0])
                                    
                                except:
                                    #I want to put a nan if its not floatable
                                    athlete_database[athlete][series][comp+"-"+day][tla][value] = 0.0
    
                            #My table now has E score dont need to do math
                            # D = athlete_database[athlete][comp][day][tla][order[0]]
                            # Score = athlete_database[athlete][comp][day][tla][order[3]]
                            # #Score is D + E
                            
                            # try:
                            #     E = float(Score) - float(D)
                            #     E = athlete_database[athlete][comp][day][tla][order[1]]
                            #     #print(f"Score: {float(Score)}, D: {float(D)}")
                            # except:
                            #     E = np.nan
                            # #print(E)
                            # try:
                            #     athlete_database[athlete][comp][day][tla][Ename] = float(E)
                            # except:
                            #     athlete_database[athlete][comp][day][tla][Ename] = str(E)
            else:
                pass
                # they did not compete in this competion
                # print(f"{athlete} did not compete at {comp}")
         
#%% Let's now add some statistical information to the database!

#two values of interest for each competition:
# 1: average
# 2: best
#now adding a third:
# 3: combined

# global interest? eventually average of all and best of all... TODO but later

#method: sweep through athletes, competition, and days.
#do math to get average and best, save that data
#will only do for score (could be done to get highest D score, E score... not now)

#loop through athletes
for athlete in athletes:
    #loop through competitions
    # for series in comp_overview
    for series in competition_series:
        for comp in comp_overview[series]['SR']:
            
            athlete_database[athlete][series]['average'] = {}
            athlete_database[athlete][series]['best'] = {}
            athlete_database[athlete][series]['combined'] = {}
            
            #remember that not all athletes compete at all compettions
            #check to see if there is an entry for that comp
            # try: if athlete_database[athlete][comp]:
            for day in days:
                comp_day = comp+"-"+day
                # if comp_day in athlete_database.get(athlete, {}).get(series, {}):
                #     # print(f"{athlete} competed at {comp}")
                #     # complete statistical analysis for the days they competed
                #     # keep in mind they may not have competed on all events on all days
                    
                #     # athlete_database[athlete][series]['average'] = {}
                #     # athlete_database[athlete][series]['best'] = {}
                #     # athlete_database[athlete][series]['combined'] = {}
                    
                for tla in tlas:
                    #query the dataframe to obtain all data
                    athlete_database[athlete][series]['average'][tla] = {}
                    athlete_database[athlete][series]['best'][tla] = {}
                    athlete_database[athlete][series]['combined'][tla] = {}
                    
                    for value in order: #+[Ename]:#forgot that I was treating E score differently
                        #sweep through all days, do not include category keys
                        results = [key for key in athlete_database[athlete][series].keys() if key not in ["category","country","average","best","combined"]]
                        
                        vals = []
                        
                        for result in results:
                            # print(f"result: {result}")
                            val = athlete_database[athlete][series][result][tla][value]
                            # if it is a zero, make it a nan
                            #sometimes now I have nan for bonus or ND
                            #but i want the math to math
                            if math.isnan(val) and not(math.isnan(athlete_database[athlete][series][result][tla]["D"])): 
                                #we have data for this event, but this bonus or ND is nan, lets turn it to zero for calcs to make sense
                                print("made it here")
                                val = 0.0
                            elif val == 0:
                                #dont know if i still need this, but keeping in case
                                val = np.nan
                            vals.append(val)
                        
                        #Now, let's get the mean and max values and store in new database
                        #because some values might be nans (if did not compete)
                        #use nanmean and nanmax so it ignores them
                        #however, if all vals are nan, then just put nan
                        # print(f"vals: {vals}")
                        
                        # Check if all values are NaN
                        
                        #I want to filter by Best final scores...
                        #I think best will need to be dealth with differently.
                        
                        if np.all(np.isnan(vals)):
                            #if they are all nans, set to zero... #TODO test if id rather them be nans?
                            #it messes up my D vs. E score plot unfortunately right now
                            athlete_database[athlete][series]['average'][tla][value] = np.nan #0.0
                            athlete_database[athlete][series]['best'][tla][value] = np.nan #0.0
                            athlete_database[athlete][series]['combined'][tla][value] = np.nan #0.0
                            
                        else:
                            athlete_database[athlete][series]['average'][tla][value]= np.nanmean(vals)
                            athlete_database[athlete][series]['best'][tla][value] = np.nanmax(vals)
                            athlete_database[athlete][series]['combined'][tla][value] = np.nansum(vals)
    
                else:
                    # print(f"{athlete} did not compete at {comp}")
                    pass

#%% re format comp_overview
#for each competition, extract categories
for series in competition_series:
    comp_overview[series] = {}
    for category in categories:
        comp_overview[series][category] = []
        for comp in competitions:
            for day in days:
                comp_overview[series][category].append(comp+"-"+day) #+"-"+day)


#%% I want to pickle my database 

# File path to save the pickled database
# database_filename = "CottbusEF_mag_athletes"
path = "production_data/WorldChamps2025"
os.makedirs(path, exist_ok=True)
database_filename = "WorldChamps2025_athletes_R1"
file_path = path+"/"+database_filename

# Pickle the database
with open(file_path, 'wb') as f:
    pickle.dump(athlete_database, f)

print("Database pickled successfully.")
