#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 17:49:30 2025

@author: joelgagnon
"""
#%%
# some notes:
#     There is inconsistencies between books:
#     some have penalty first, bonus second, others vice versa
# some books have commas between names, others dont!
# some country codes not in the list... kind of want to get rid of that check
# some books dont have "RANK" at the top, instead No.

#Osijek and Cairo, data problems with vault
#Doha doesnt work well for some DNS results - need to decide how to treat that
#%%

# #now need these for attempt at creating a server to get it to open to right page
import http.server
import socketserver
import threading


#these two for opening up csvs and editing 
import subprocess
import platform

#needed to open a pdf in a browser
import webbrowser

#for a random sleep 
import time


import os
from country_codes import VALID_COUNTRY_CODES
import pdfplumber
import pandas as pd
import re  # For checking country codes

path = "test_data/WorldCups2025"
competitions = ["COTTBUS","DOHA","OSIJEK","BAKU","CAIRO","ANTALYA"]
# competitions = ["OSIJEK"]  #,"BAKU"] 
# competitions = ["COTTBUS","ANTALYA"]
# competitions = ["COTTBUS","DOHA","OSIJEK","ANTALYA"]
#osijek and cairo have vault problems
#antalya data seems odd with final scores
events = ["FX","PH","SR","VT","PB","HB"]
# events = ["VT"]
days = ["QF","EF"]
# days = ["QF"]

#osijek, no bib numbers
#baku and cairo VT problems

#create some dictionaries that contain page numbers on pdf for the events
Cottbus_dict = {"QF":{"FX":[12],"PH":[15],"SR":[17],"VT":[19,20],"PB":[22],"HB":[24]},
                "EF":{"FX":[26],"PH":[28],"SR":[30],"VT":[32],"PB":[34],"HB":[36]},
                }
            
Baku_dict = {"QF":{"FX":[29],"PH":[30],"SR":[32],"VT":[34],"PB":[35],"HB":[37]},
             "EF":{"FX":[41],"PH":[43],"SR":[45],"VT":[47],"PB":[49],"HB":[51]},
                }

Antalya_dict = {"QF":{"FX":[16],"PH":[18],"SR":[20],"VT":[22],"PB":[23],"HB":[25]},
                "EF":{"FX":[35],"PH":[36],"SR":[38],"VT":[39],"PB":[40],"HB":[41]},
                }

Osijek_dict = {"QF":{"FX":[20],"PH":[22,23],"SR":[25],"VT":[27,28],"PB":[29],"HB":[31]},
               "EF":{"FX":[40],"PH":[43],"SR":[45],"VT":[47],"PB":[50],"HB":[52]},
                }

Doha_dict = {"QF":{"FX":[17],"PH":[18],"SR":[19],"VT":[20],"PB":[21],"HB":[22]},
             "EF":{"FX":[30],"PH":[31],"SR":[32],"VT":[34],"PB":[35],"HB":[36]},
                }

Cairo_dict = {"QF":{"FX":[33],"PH":[34],"SR":[35],"VT":[36],"PB":[37],"HB":[38]},
              "EF":{"FX":[47],"PH":[48],"SR":[49],"VT":[50],"PB":[51],"HB":[52]},
              }

#create nested dictionary
wc_dict = {
    "COTTBUS": Cottbus_dict,
    "DOHA": Doha_dict,
    "OSIJEK": Osijek_dict,
    "BAKU": Baku_dict,
    "CAIRO": Cairo_dict,
    "ANTALYA": Antalya_dict,
}

#%% Helpful Functions

# Function to check if a string is a three-letter country code (all caps)
def is_country_code(entry):
    return entry in VALID_COUNTRY_CODES

# Function to check if a value is a valid numeric score (allows decimal commas)
def is_score(value):
    return bool(re.fullmatch(r"\d+,\d+|\d+\.\d+", value))


def format_scores(unformatted_scores):
    #unformatted_scores is a list
    scores = [val.replace(",", ".") for val in unformatted_scores if is_score(val) or "-" in val or "+" in val or "(" in val]
    return scores

#function to try and edit csvs that are flagged
def open_file(filepath):
    if platform.system() == "Darwin":  # macOS
        subprocess.call(('open', filepath))
    elif platform.system() == "Windows":
        os.startfile(filepath)
    elif platform.system() == "Linux":
        subprocess.call(('xdg-open', filepath))
        
#%% Score Sanity Checker

def score_checker(Score, Dscore,Escore,Penalty=0.0,Bonus=0.0):
    #function that checks if score adds up
    #Penatly and Bonus are optional inputs
    #convert all to floats
    if Penalty == "":
        Penalty = 0.0
    if Bonus == "":
        Bonus = 0.0
    
    S = float(Score)
    D = float(Dscore)
    E = float(Escore)
    P = float(Penalty)
    B = float(Bonus)
    if S == E + E +P + B:
        return True
    else:
        return False

#%% For post processing csvs

first_loop = True


#%%

#keywords to search for beginning of table
keywords = ["RANK","NO.","#"]

for comp in competitions:
    print("=============")
    print(f"{comp} RESULTS")
    print("=============")
    file_path = f"{path}/{comp}_RESULTS.pdf"
    
    #open pdf
    # pages_to_extract = [12,15,17,19,20,22,24]
    
    with pdfplumber.open(file_path) as pdf:
        for day in days:
            print(f"{day}:")
            for event in events:
                print(f"   {event}")
                pages_to_extract = wc_dict[comp][day][event]
                table_data = []
                for j,page_number in enumerate(pages_to_extract):
                    page = pdf.pages[page_number]
                    text = page.extract_text()

                    lines = text.split("\n")
                    
                    if j==0:
                        start_idx = next((i for i, line in enumerate(lines) if any(keyword in line.upper() for keyword in keywords)), None)
                    else:
                        #in this case, we are on the second page, and the start idx could be Vault 1 or Vault 2
                        special_keywords = keywords + ["Vault"]
                        start_idx = next((i for i, line in enumerate(lines) if any(keyword in line.upper() for keyword in special_keywords)), None)
                    # if start_idx is not None and start_idx + 1 < len(lines):
                        
                    if start_idx + 1 < len(lines):
                        page_data = lines[start_idx + 1 :]  # Start from the next line
                    else:
                        print("Table start not found.")
                        page_data = []
                    #add table_data to all_table_data    
                    table_data.extend(page_data)
                    
                #Noe
                # Process table data, ignoring lines that start with "Print"
                cleaned_data = []
                
                if event == "VT":  # Special handling for Vault
                    i = 0
                    while i < len(table_data):
                        row = table_data[i].strip()
        
                        if not row or row.startswith("Print"):
                            i += 1
                            continue  # Skip empty or unwanted lines
        
                        split_row = row.split()
        
                        if len(split_row) < 3 or not split_row[0].isdigit():
                            i += 1
                            continue  # Skip invalid rows
                        
                        # Extract Rank, BIB, Name, Country, and Total Score
                        rank = split_row[0]
                        bib_number = split_row[1]
                        name_parts = split_row[2:-2]  # Everything except last two (country, total score)
                        country = split_row[-2]
                        total_score = split_row[-1].replace(",", ".")
        
                        full_name = " ".join(name_parts).strip()
                        last_name, first_name = full_name.split(",", 1) if "," in full_name else (full_name, "")
                        
                        #Trying to change the vault data
                        #typically it has the world Vault 1 and Vault 2 
                        #afterwards there could be up to 5 entries
                        
                        # Move to Vault 1 details
                        i += 1
                        
                        if i < len(table_data)-1:
                            
                            #check that the first entry is a score or says Vault
                            try:
                                score = float(table_data[i].split()[0])
                                # if not(is_score(float(table_data[i].split()[0]))):
                                #     print("score is a float but not a valid score")
                            except:
                                counter = 0
                                while table_data[i].split()[0]!="Vault":
                                    counter+=1
                                    i+=1
                                    if (counter > 10) or (i > len(table_data)-1):
                                        print("while loop for vault checker took over 10 times bro check line 177")
                                        break
                            
                            
                            if table_data[i].split()[0]=="Vault":
                                vault1 = format_scores(table_data[i].split()[2:]) #the [2:] makes sure we remove the first two entries "Vault" and "1"
                            else:
                                vault1 = format_scores(table_data[i].split())
                            #right away let
                            D1, E1, Penalty1, Bonus1, Score1 = ["", "", "", "", ""]
                            
                            # Remove "Vault 1" if it's mistakenly captured
                            
                            try:
                                D1, E1, *rest, Score1 = vault1
        
                                if not is_score(D1):  # Ensure it's a valid score
                                    D1 = ""
                                if not is_score(E1):  # Ensure it's a valid score
                                    E1 = ""
                                Score1 = Score1.replace(",", ".")  # Convert decimal comma to period
        
                                for value in rest:
                                    clean_value = re.sub(r"[()+]", "", value)  # Remove ( ) and +
                                    if "-" in value or value.startswith("0."):  # Negative or 0.x = Penalty
                                        Penalty1 = format_scores([clean_value])[0]
                                    elif "+" in value or value.startswith("0."):  # Positive or 0.x = Bonus
                                        Bonus1 = format_scores([clean_value])[0]
                            except:
                                print("vault 1 data error")
                                
                            # Move to Vault 2 details
                            i += 1
                            
                            if i < len(table_data)-1:   
                                try:
                                    score = float(table_data[i].split()[0])
                                    # if not(is_score(float(table_data[i].split()[0]))):
                                    #     print("score is a float but not a valid score")
                                except:
                                    counter = 0
                                    while table_data[i].split()[0]!="Vault":
                                        counter+=1
                                        i+=1
                                        if (counter > 10) or (i > len(table_data)-1):
                                            print("while loop for vault checker took over 10 times bro check line 209")
                                            break
                                        
                            if i < len(table_data):       
                                if table_data[i].split()[0]=="Vault":
                                    vault2 = format_scores(table_data[i].split()[2:])
                                else:
                                    vault2 = format_scores(table_data[i].split())
                                    
                                D2, E2, Penalty2, Bonus2, Score2 = ["", "", "", "", ""]
                                
                                # Remove "Vault 2" if it's mistakenly captured
                                # vault2 = [v for v in vault2 if "Vault" not in v]
                                
                                if "DNS" in table_data[i]:
                                    vault2 = ["", "", "", "", ""]
                                
                                try:
                                    D2, E2, *rest, Score2 = vault2
                                    if not is_score(D2):  # Ensure it's a valid score
                                        D2 = ""
                                    if not is_score(E2):  # Ensure it's a valid score
                                        E2 = ""
                                    Score2 = Score2.replace(",", ".")  # Convert decimal comma to period
            
                                    for value in rest:
                                        clean_value = re.sub(r"[()+]", "", value)  # Remove ( ) and +
                                        if "-" in value or value.startswith("0."):  # Negative or 0.x = Penalty
                                            Penalty2 = format_scores([clean_value])[0]
                                        elif "+" in value or value.startswith("0."):  # Positive or 0.x = Bonus
                                            Bonus2 = format_scores([clean_value])[0]
                                except:
                                    print("vault 2 data error")
                            
                            #Score sanity checks
                            #format i want is penalty to be negative, bonus positive
                            #sometimes things are so bad that we dont have strings that are scores, so put ina  try except 
                            try:
                                if score_checker(Score1, D1, E1, Penalty1, Bonus1) == False:
                                    #first thing to check is if penalty is negaive
                                    if Penalty1 != "":
                                        if float(Penalty1) > 0.0:
                                            Penalty1 = -float(Penalty1)
                                        #now check again:
                                    if score_checker(Score1, D1, E1, Penalty1, Bonus1):
                                        print(f"tried making penalty negative, still aint adding up for VT1")
                            except:
                                print(f"Major Error: Score Checker failed got {last_name}, {first_name}!")
                            try:
                                if score_checker(Score2, D2, E2, Penalty2, Bonus2) == False:
                                    #first thing to check is if penalty is negaive
                                    if Penalty2 != "":
                                        if float(Penalty2) > 0.0:
                                            Penalty2= -float(Penalty2)
                                        #now check again:
                                    if score_checker(Score2, D2, E2, Penalty2, Bonus2):
                                        print(f"tried making penalty negative, still aint adding up for VT1")
                            except:
                                print(f"Major Error: Score Checker failed got {last_name}, {first_name}!")

                            
                            # Store cleaned data
                            cleaned_data.append([rank, bib_number, last_name.strip(), first_name.strip(), country,
                                                 D1, E1, Penalty1, Bonus1, Score1,
                                                 D2, E2, Penalty2, Bonus2, Score2, total_score])
            
                            i += 1  # Move to next entry
                    
                    # Convert VT data into DataFrame
                    df = pd.DataFrame(cleaned_data, columns=["Rank", "BIB", "Last Name", "First Name", "Country",
                                                             "VT1_D", "VT1_E", "VT1_ND", "VT1_Bonus", "VT1_Score",
                                                             "VT2_D", "VT2_E", "VT2_ND", "VT2_Bonus", "VT2_Score",
                                                             "VT_Score"])
                else: #any event except vault
                    for row in table_data:
                        if row.strip().startswith("Print"):  # Ignore "Print" lines
                            continue
                        
                        split_row = row.split()
                    
                        if not split_row:
                            continue  # Skip empty rows
                    
                        # Remove first column if it contains only numbers (rank)
                        if split_row[0].isdigit() and comp != "OSIJEK": #osijek data had rank but not bib, and messes up naming logic
                            split_row.pop(0)
                    
                        # Identify the country code index
                        country_idx = next((i for i, entry in enumerate(split_row) if is_country_code(entry)), None)
                    
                        if country_idx is None:
                            print(f"check if {split_row} has a valid country code")
                            continue  # Skip row if no country code found
                    
                        # Extract BIB number (first entry)
                        bib_number = split_row[0]
                    
                        # Everything between BIB and country code is the full name
                        full_name_parts = split_row[1:country_idx]
                        
                        # Join into a single string
                        full_name = " ".join(full_name_parts).strip()
                        
                        # Handle Last Name and First Name correctly
                        if "," in full_name:
                            parts = full_name.split(",", maxsplit=1)  # Split at the first comma
                            last_name = parts[0].strip()  # Everything before the comma (Last Name)
                            first_name = parts[1].strip()  # Everything after the comma (First Name)
                        else:
                            # If there's no comma, assume the full name is missing a clear split
                            name_parts = full_name.split()
                            
                            # If there's at least one all-uppercase word, assume those are the last name
                            upper_parts = [p for p in name_parts if p.isupper()]
                            lower_parts = [p for p in name_parts if not p.isupper()]
                         
                            if upper_parts:
                                last_name = " ".join(upper_parts)
                                first_name = " ".join([p for p in name_parts if p not in upper_parts])
                            elif len(name_parts) > 1:
                                # Fallback: Assume last word is first name
                                last_name = " ".join(name_parts[:-1])
                                first_name = name_parts[-1]
                            else:
                                # Single word, assume it's the last name
                                last_name = full_name
                                first_name = ""
                            
                            #make last name upper regardless
                            last_name = last_name.upper()
                            #in this case, its lower case and its in reverse
                        
                        # print(f"first: {first_name}")
                        # print(f"last: {last_name}")
                        # Country code
                        country = split_row[country_idx]
                    
                        # Convert numeric values (after the country column) from comma to point format
                        unformatted_scores = split_row[country_idx + 1:]
                        scores = format_scores(unformatted_scores)
                        # scores = [val.replace(",", ".") for val in unformatted_scores if is_score(val) or "-" in val or "+" in val or "(" in val]
                    
                        # Default structure
                        D_score, E_score, penalty, bonus, final_score = "", "", "", "", ""
                    
                        if len(scores) >= 2:  # At least D & E scores exist
                            D_score, E_score = scores[:2]
                    
                        if len(scores) >= 3:  # Final score is always the last one
                            final_score = scores[-1]
                    
                        # Look for penalties & bonuses in between
                        middle_scores = scores[2:-1] if len(scores) > 3 else []  # Between E and Final
                    
                        for value in middle_scores:
                            clean_value = re.sub(r"[()+]", "", value)  # Remove ( ) and +
                            if "-" in value or value.startswith("0."):  # Negative or 0.x = Penalty
                                penalty = format_scores([clean_value])[0]
                            elif "+" in value or value.startswith("0."):  # Positive or 0.x = Bonus
                                bonus = format_scores([clean_value])[0]
                                
                                
                        #Score sanity checks
                        #format i want is penalty to be negative, bonus positive
                        #sometimes things are so bad that we dont have strings that are scores, so put ina  try except 
                        try:
                            if score_checker(final_score, D_score, E_score, penalty, bonus) == False:
                                #first thing to check is if penalty is negaive
                                if penalty != "":
                                    if float(penalty) > 0.0:
                                        penalty = -float(penalty)
                                    #now check again:
                                if score_checker(final_score, D_score, E_score, penalty, bonus):
                                    print(f"tried making penalty negative, still aint adding up")
                        except:
                            print(f"Major Error: Score Checker failed got {last_name}, {first_name}!")
                        
                        # Ensure exactly 9 columns per row
                        cleaned_row = [bib_number, last_name, first_name, country, D_score, E_score, penalty, bonus, final_score]
                        cleaned_data.append(cleaned_row[:9])  # Trim any extra values
                        
                        # Convert to DataFrame with proper column names
                        df = pd.DataFrame(cleaned_data, columns=["BIB", "Last Name", "First Name", "Country", "D Score", "E Score", "Penalty", "Bonus", "Final Score"])
                
                    
                    
                # Save to CSV or print
                check_em_all = True #new option that will go through one by one
                check_csvs = False
                edit_csvs = False
                
                #options to view all display rows and columns for data frame
                pd.set_option('display.max_columns', None)
                pd.set_option('display.max_rows', None)

                # Show more characters per line (default is 80 or 100)
                pd.set_option('display.width', 200)  # Try 200 or 300 depending on your screen
                
                # Also increase column width if needed
                pd.set_option('display.max_colwidth', None)
                
                # Ensure all columns are visible (just in case)
                pd.set_option('display.max_columns', None)


                #if i want to return to default
                # pd.reset_option('display.max_columns')
                # pd.reset_option('display.max_rows')
                
                if check_em_all:
                    #no need to preview, lets just go ahead and make the file and open it
                    path = f"{comp}_csv/{comp}_{day}_{event}.csv"
                    os.makedirs(f"{comp}_csv/f", exist_ok=True)
                    df.to_csv(path, index=False, encoding='utf-8')
                    print(f"opening {path}...")
                    open_file(path)
                    cwd = os.getcwd()
                    page_display = pages_to_extract[0] + 1 #python is index at 0
                    url = f"file:///{cwd}/{file_path}#page={page_display}"
                    
                    # === CONFIGURATION ===
                    PORT = 8000
                    
                    # === Construct URL ===
                    file_url = f"http://localhost:{PORT}/{file_path}#page={page_display}"
                    
                    
                    # === Start HTTP server in a thread ===
                    def start_server():
                        handler = http.server.SimpleHTTPRequestHandler
                        with socketserver.TCPServer(("", PORT), handler) as httpd:
                            print(f"Serving at http://localhost:{PORT}")
                            httpd.serve_forever()
                            
                    if first_loop:
                        server_thread = threading.Thread(target=start_server, daemon=True)
                        server_thread.start()
                    
                        # Give server time to start
                        time.sleep(1)
                        
                        #change first_loop flag
                        first_loop=False
                    
                    # === Open in Google Chrome ===
                    chrome_path = "open -a 'Google Chrome'"  # Mac-specific
                    os.system(f"{chrome_path} '{file_url}'")
                    
                    # === Wait for user to close server ===
                    input("Press Enter to stop the server and exit...\n")
                    
                    
                    
                    #Can open in chrome but not respecting page display
                    # chrome_path = "open -a 'Google Chrome'"
                    # webbrowser.get(chrome_path).open(url)
                    
                    # subprocess.run(["open", "-a", "Google Chrome", url])
                    # # Wait a moment
                    # time.sleep(2)
                    
                    # # Re-open to force page anchor to apply
                    # subprocess.run(["open", "-a", "Google Chrome", url])
                    
                    # Try safari
                    # subprocess.run(["open", "-a", "Safari", url])
                    
                    
                elif check_csvs:
                    #we want to view the dataframe to see if there are any errors
                    print(f"\n----- Preview: {comp}_{day}_{event} -----")
                    print(df)  # Show first 10 rows
                    # print(df.columns)   # Show column headers
                    
                    # Ask user to confirm if it should be saved
                    response = input("Save this file? (y for yes, anything else to flag): ").strip().lower()
                    
                    if response == 'y':
                        os.makedirs(f"{comp}_csv", exist_ok=True)
                        df.to_csv(f"{comp}_csv/{comp}_{day}_{event}.csv", index=False, encoding='utf-8')
                        print("Saved ✅")
                    else:
                        flagged_path = f"{comp}_csv/flagged/{comp}_{day}_{event}.csv"
                        os.makedirs(f"{comp}_csv/flagged/", exist_ok=True)
                        df.to_csv(flagged_path, index=False, encoding='utf-8')
                        print(f"Flagged for review 🚩 — saved to: {flagged_path}")
                        if edit_csvs:
                            open_file(flagged_path)
                            cwd = os.getcwd()
                            page_display = pages_to_extract[0] + 1 #python is index at 0
                            url = f"file:///{cwd}/{file_path}#page={page_display}"
                            
                            # === CONFIGURATION ===
                            PORT = 8000
                            
                            # === Construct URL ===
                            file_url = f"http://localhost:{PORT}/{file_path}#page={page_display}"
                            
                            # === Start HTTP server in a thread ===
                            # def start_server():
                            #     handler = http.server.SimpleHTTPRequestHandler
                            #     with socketserver.TCPServer(("", PORT), handler) as httpd:
                            #         print(f"Serving at http://localhost:{PORT}")
                            #         httpd.serve_forever()
                                    
                            server_thread = threading.Thread(target=start_server, daemon=True)
                            server_thread.start()
                            
                            # Give server time to start
                            time.sleep(1)
                            
                            # === Open in Google Chrome ===
                            chrome_path = "open -a 'Google Chrome'"  # Mac-specific
                            os.system(f"{chrome_path} '{file_url}'")
                            
                            # === Wait for user to close server ===
                            input("Press Enter to stop the server and exit...\n")
                            
                            # === Proper shutdown ===
                            if httpd:
                                httpd.shutdown()
                                httpd.server_close()
                                print("Server shut down.")
                            
                            
                            #Can open in chrome but not respecting page display
                            # chrome_path = "open -a 'Google Chrome'"
                            # webbrowser.get(chrome_path).open(url)
                            
                            # subprocess.run(["open", "-a", "Google Chrome", url])
                            # # Wait a moment
                            # time.sleep(2)
                            
                            # # Re-open to force page anchor to apply
                            # subprocess.run(["open", "-a", "Google Chrome", url])
                            
                            # Try safari
                            subprocess.run(["open", "-a", "Safari", url])
                            
                            
                            # webbrowser.open_new(f"file:///{cwd}/{file_path}#page={page_number}")
                
                else:
                    # Create directory if it doesn't exist
                    os.makedirs(comp+"_csv", exist_ok=True)
                    #forcing encoding to be utf-8 to work with more alphabets
                    df.to_csv(f"{comp}_csv/{comp}_{day}_{event}.csv", index=False,encoding='utf-8')
                    # print(f"      saved")
                    # print(df)
                
                #
