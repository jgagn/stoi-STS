#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 17:49:30 2025

@author: joelgagnon
"""

from country_codes import VALID_COUNTRY_CODES
import pdfplumber
import pandas as pd
import re  # For checking country codes

path = "test_data/WorldCups2025"
competitions = ["COTTBUS","DOHA","OSIJEK","BAKU","CAIRO","ANTALYA"]
competitions = ["COTTBUS"]
events = ["FX","PH","SR","VT","PB","HB"]
# events = ["VT"]
days = ["QF","EF"]
# days = ["QF"]

event="FX"

for comp in competitions:
    print("=============")
    print(f"{comp} RESULTS")
    print("=============")
    file_path = f"{path}/{comp}_RESULTS.pdf"
    
    #open pdf
    pages_to_extract = [12,15,17,19,20,22,24]
    with pdfplumber.open(file_path) as pdf:
        for i in pages_to_extract:
            page = pdf.pages[i]
            text = page.extract_text()
    
    #%% OLD
        
            # Find the index where "RANK" appears and start from the next line
            lines = text.split("\n")
            start_idx = next((i for i, line in enumerate(lines) if "RANK" in line.upper()), None)
            
            # if start_idx is not None and start_idx + 1 < len(lines):
            if start_idx + 1 < len(lines):
                table_data = lines[start_idx + 1 :]  # Start from the next line
            else:
                print("Table start not found.")
                table_data = []
            
            # Function to check if a string is a three-letter country code (all caps)
            def is_country_code(entry):
                return entry in VALID_COUNTRY_CODES
            
            # Function to check if a value is a valid numeric score (allows decimal commas)
            def is_score(value):
                return bool(re.fullmatch(r"\d+,\d+|\d+\.\d+", value))
            
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
    
                    # Move to Vault 1 details
                    i += 1
                    vault1 = table_data[i].split()
                    D1, E1, Penalty1, Bonus1, Score1 = ["", "", "", "", ""]
                    
                    # Remove "Vault 1" if it's mistakenly captured
                    
                    if len(vault1) >= 5:
                        D1, E1, *rest, Score1 = vault1[-5:]
                        if not is_score(D1):  # Ensure it's a valid score
                            D1 = ""
                        if not is_score(E1):  # Ensure it's a valid score
                            E1 = ""
                        Score1 = Score1.replace(",", ".")  # Convert decimal comma to period
                        for val in rest:
                            if "-" in val or val.startswith("0,"):
                                Penalty1 = val.replace(",", ".")
                            elif "+" in val:
                                Bonus1 = val.replace(",", ".")
                    
                    # Move to Vault 2 details
                    i += 1
                    vault2 = table_data[i].split()
                    D2, E2, Penalty2, Bonus2, Score2 = ["", "", "", "", ""]
                    
                    # Remove "Vault 2" if it's mistakenly captured
                    vault2 = [v for v in vault2 if "Vault" not in v]
                    
                    if len(vault2) >= 5:
                        D2, E2, *rest, Score2 = vault2[-5:]
                        if not is_score(D2):  # Ensure it's a valid score
                            D2 = ""
                        if not is_score(E2):  # Ensure it's a valid score
                            E2 = ""
                        Score2 = Score2.replace(",", ".")  # Convert decimal comma to period
                        for val in rest:
                            if "-" in val or val.startswith("0,"):
                                Penalty2 = val.replace(",", ".")
                            elif "+" in val:
                                Bonus2 = val.replace(",", ".")
    
                    # Store cleaned data
                    cleaned_data.append([rank, bib_number, last_name.strip(), first_name.strip(), country,
                                         D1, E1, Penalty1, Bonus1, Score1,
                                         D2, E2, Penalty2, Bonus2, Score2, total_score])
    
                    i += 1  # Move to next entry
                
                # Convert VT data into DataFrame
                df = pd.DataFrame(cleaned_data, columns=["Rank", "BIB", "Last Name", "First Name", "Country",
                                                         "D1", "E1", "Penalty1", "Bonus1", "Score1",
                                                         "D2", "E2", "Penalty2", "Bonus2", "Score2",
                                                         "Total Score"])
            else:
                for row in table_data:
                    if row.strip().startswith("Print"):  # Ignore "Print" lines
                        continue
                    
                    split_row = row.split()
                
                    if not split_row:
                        continue  # Skip empty rows
                
                    # Remove first column if it contains only numbers (rank)
                    if split_row[0].isdigit():
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
                        if len(name_parts) > 1:
                            last_name = " ".join(name_parts[:-1])  # Everything except the last word
                            first_name = name_parts[-1]  # The last word is the first name
                        else:
                            last_name = full_name
                            first_name = ""
                    # Country code
                    country = split_row[country_idx]
                
                    # Convert numeric values (after the country column) from comma to point format
                    scores = [val.replace(",", ".") for val in split_row[country_idx + 1:] if is_score(val) or "-" in val or "+" in val or "(" in val]
                
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
                            penalty = clean_value
                        elif "+" in value or value.startswith("0."):  # Positive or 0.x = Bonus
                            bonus = clean_value
                
                    # Ensure exactly 9 columns per row
                    cleaned_row = [bib_number, last_name, first_name, country, D_score, E_score, penalty, bonus, final_score]
                    cleaned_data.append(cleaned_row[:9])  # Trim any extra values
                    
                    # Convert to DataFrame with proper column names
                    df = pd.DataFrame(cleaned_data, columns=["BIB", "Last Name", "First Name", "Country", "D Score", "E Score", "Penalty", "Bonus", "Final Score"])
            
            
            
            # Save to CSV or print
            df.to_csv(f"Cottbus_{i}.csv", index=False)
            print(df)
