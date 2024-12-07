#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 14 09:44:49 2024

@author: joelgagnon
"""

#%% Description

#file which contains algorithm to calculate team score 

#%% imports
import math
import numpy as np
from termcolor import colored, cprint
from tabulate import tabulate
#%% global variables
tlas = ["FX","PH","SR","VT1","PB","HB","AA"]
order = ["D","Score","Rank"]
Ename = "E"
apparatus = ["Floor","Pommel Horse","Rings","Vault #1","Parallel Bars","High Bar","AllAround"]

#%% Algorithm to Calculate Team Scores

#I need to add the results to use for the calcs: "day1","day2","average" or "best"
# results = "average"

def team_score_calcs(comp_format,team,database,competition,results='average',print_table=False):
    if len(team) != comp_format[0]:
        #If given a team, check the format is compatible
        print(f"Error: {len(team)} members given when {comp_format[0]}-{comp_format[1]}-{comp_format[2]} format given!")
    else:
        #let's decide who's up on each event
        #easier to decide who to dump 
        #from comp format we decide which scores to not compete
        #we also decide which scores to count
        #HOWEVER, there may be a scenario where you want an all arounder, so keep that in mind
        drop = comp_format[0] - comp_format[1]
        dont_count = comp_format[1] - comp_format[2]
        team_scores = {}
        for athlete in team:
            team_scores[athlete] = {}
        #sweep through events
        for tla in tlas[0:6]:
            #we need to "drop" and potentially "not count" some scores
            #add all scores, BUT, 
            for athlete in team:
                #starting with day1 results, later we allow day 1, day 2, 2 day or best out of 2
                #However, if the score is nan, change to 0.0
                if math.isnan(database[athlete][competition][results][tla][order[1]]):
                    score = 0.0
                else:
                    score = database[athlete][competition][results][tla][order[1]]
                team_scores[athlete][tla] = [score,"TBD"]
    
        #let determine who is not competing what events
        if comp_format[0] > comp_format[1]:
            #do the calc to see who doesnt compete
            #could be more than 1
            #example of course is NCAA with 15-6-5 or 15-5-5 format
            #TODO will need some tie breakers... 
            not_competing = comp_format[0] - comp_format[1]
            #print(f"not competing: {not_competing}")
            #for each event, drop lowest score(s)
            for tla in tlas[0:6]:
                #check all scores that are "TBD"
                #add them to a list variable
                scores = []
                for athlete in team:
                    if team_scores[athlete][tla][1] == "TBD":
                        #print(f"team_scores[athlete][tla][0]: {team_scores[athlete][tla][0]}")
                        scores.append(team_scores[athlete][tla][0])
                #sort the scores (smallest to largest)
                scores.sort()
                #print(f"scores: {scores}")
                #determine scores that wont be competing
                dropped_scores = scores[0:not_competing]
                #now go intot the list and if the score is dropped, marked as so
                #print(f"dropped scores: {dropped_scores}")
                for athlete in team:
                    if team_scores[athlete][tla][0] in dropped_scores:
                        #what if there's a tie?
                        #print(team_scores[athlete][tla][0])
                        #need to remove this score from the dropped_scores list!
                        dropped_scores.remove(team_scores[athlete][tla][0])
                        #update the athlete's competition status
                        team_scores[athlete][tla][1] = "scratch" #does not compete or does not count
    
        else:
            #everyone competes!
            pass
        
        #lets see who's scores get dropped!
        if comp_format[1] > comp_format[2]:
            # repeat
            # what was done but instead of scratch we just say the score is dropped
            #do the calc to see who doesnt compete
            #could be more than 1
            #example of course is NCAA with 15-6-5 or 15-5-5 format
            #TODO will need some tie breakers... 
            dropped = comp_format[1] - comp_format[2]
            #print(f"scores being dropped: {dropped}")
            #for each event, drop lowest score(s)
            for tla in tlas[0:6]:
                #check all scores that are "TBD"
                #add them to a list variable
                scores = []
                for athlete in team:
                    if team_scores[athlete][tla][1] == "TBD":
                        scores.append(team_scores[athlete][tla][0])
                #sort the scores (smallest to largest)
                scores.sort()
                #determine scores that wont be competing
                dropped_scores = scores[0:dropped]
                #now go intot the list and if the score is dropped, marked as so
                for athlete in team:
                    if team_scores[athlete][tla][0] in dropped_scores:
                        #what if there's a tie?
                        #Need to check that the score is is still TBD!
                        if team_scores[athlete][tla][1] == "TBD":
                            #need to remove this score from the dropped_scores list!
                            dropped_scores.remove(team_scores[athlete][tla][0])
                            #update the athlete's competition status
                            team_scores[athlete][tla][1] = "dropped" #does not compete or does not count
                        else:
                            #in this case, score may have already been scratched!
                            pass
        else:
            #all competing scores count
            #change all TBDs to counting scores
            pass
        
        #Any TBDs left have survived and are competing!
        #Lets loop through, calculate event totals and change TBDs to counting
        event_totals = {}
        overall_score = 0.0
        team_scores['Team'] = {}
        for tla in tlas[0:6]:
            #initialize event totals
            event_totals[tla] = 0.0
            for athlete in team:
                if team_scores[athlete][tla][1] == "TBD":
                    team_scores[athlete][tla][1] = "counting"
                    event_totals[tla] += team_scores[athlete][tla][0]
                    overall_score += team_scores[athlete][tla][0]
            #save to the team scores dictionary
            team_scores['Team'][tla] = event_totals[tla]
        team_scores['Team']['AA'] = overall_score
        #Get the AA totals for each athlete
        for athlete in team:
            #initialize an AA score
            AA_score = 0.0
            for tla in tlas[0:6]:
                #only count the score if it is counting or dropped (NOT scratc)
                if team_scores[athlete][tla][1] != "scratch":
                    AA_score += team_scores[athlete][tla][0]
            #let's add an AA score
            team_scores[athlete]['AA'] = AA_score
                    
        
        #let's print the progress
        colour_dict = {"scratch":"red",
                       "dropped":"black",
                       "counting":"white"}
            
        if print_table:
            table = []
            header = []
            for athlete in team:
                new_line = [athlete]
                header.append("Athlete")
                for tla in tlas[0:6]:
                    #choose colour based on count 
                    #new_line.append(team_scores[athlete][tla][0])
                    #new_line.append(team_scores[athlete][tla][1])
                    new_line.append(colored(team_scores[athlete][tla][0],colour_dict[team_scores[athlete][tla][1]]))
                    new_line.append(colored(team_scores[athlete][tla][1],colour_dict[team_scores[athlete][tla][1]]))
                    
                    header.append(tla)
                    header.append("count")
                #We also add their AA scores
                new_line.append(team_scores[athlete]['AA'])
                header.append('Total')
                
                table.append(new_line)
            #Add subtotal
            summary_line = ["Team Total"]
            team_scores.append("Team Total")
            total = 0.0
            for event in event_totals:
                total += event_totals[event]
                summary_line.append(np.round(event_totals[event],3))
                summary_line.append("(team)")
                team_scores.append(np.round(event_totals[event],3))
                team_scores.append("(team)")
            #finally add final team SCORE!
            summary_line.append(total)
            table.append(summary_line)
            #table = [["Sun",696000,1989100000],["Earth",6371,5973.6],["Moon",1737,73.5],["Mars",3390,641.85]]
            print(tabulate(table, headers=header))
    return team_scores