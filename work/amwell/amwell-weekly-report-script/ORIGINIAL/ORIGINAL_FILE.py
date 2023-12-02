#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# import libraries
import os
import csv

import datetime
from datetime import datetime as dtm
from datetime import time as tm
from datetime import timedelta as td

import pandas as pd
import openpyxl

import pprint as pp
from IPython.display import display, HTML


# In[ ]:


# downloaded_file = 'Provider Hours 2023-07_16_To_2023-07-24.xlsx'
root_billing_folder = '/Users/aman/dev-repositories/amwell-automation'
provider_file = 'providers.xlsx'
downloaded_file = 'test.xlsx'
output_file = 'output.xlsx'
# import data
os.chdir(root_billing_folder)
hours = pd.read_excel(downloaded_file)
providers = pd.read_excel(provider_file)
print(len(hours), len(providers))
# Print end of first block with a number and all caps
print('1. END OF FIRST BLOCK'.center(100, '-'))
# Print the columns in provider file
# print(providers.columns)


# In[ ]:


# join hours df with providers df and delete duplicates, empty rows (remove non-medstar providers) 
df = hours.set_index('Provider Waiting Room Status Provider ID').join(providers.set_index('Provider ID'), how='left')
df.reset_index(level=0, inplace=True)
df.rename(columns = {'Provider Waiting Room Status Provider ID':'Provider ID'}, inplace = True)
print(df.columns)
df.drop_duplicates(['Provider Waiting Room Status UTC Event Time','Provider Waiting Room Status Status','Provider ID'],keep= 'last',inplace = True)
df = df[df['Provider Waiting Room Status Status'].notna()]
print(len(df))
# Print a table of the first 10 rows of the dataframe. Example: display(df.head(10))

# Print end of second block. Example: print('1. END OF FIRST BLOCK'.center(100, '-'))
display(df.head(20))
print('2. END OF SECOND BLOCK'.center(100, '-'))


# In[ ]:


# set datetime as index and create EST column. sort by time
pd.to_datetime(df['Provider Waiting Room Status UTC Event Time'])
df = df.set_index('Provider Waiting Room Status UTC Event Time')
df['Provider Waiting Room Status EST Event Time'] = (df.index.tz_localize('UTC').tz_convert('US/Eastern'))
df['Provider Waiting Room Status EST Event Time'] = pd.to_datetime(df['Provider Waiting Room Status EST Event Time'])
df.sort_index(inplace=True)
df.reset_index(inplace=True, drop=True)
display(df.head(20))
print('3. END OF THIRD BLOCK'.center(100, '-'))


# In[ ]:


# set waiting room status as ordered categorical series
df['Provider Waiting Room Status Status'] = pd.Categorical(df['Provider Waiting Room Status Status'], 
                                                           ["Login Status - Disconnected", "Login Status - Logged Out", 
                                                            "Login Status - Logged In", "Waiting Room - Unavailable", 
                                                            "Waiting Room - Open", "Waiting Room - On Call",
                                                            "Waiting Room - Ask Me"])
# print('3. END OF THIRD BLOCK'.center(100, '-'))

print('4. END OF FOURTH BLOCK'.center(100, '-'))


# In[ ]:


df.sort_values(by=['Provider National Provider Identifier (NPI)',
                   'Provider Waiting Room Status EST Event Time', 
                   'Provider Waiting Room Status Status'], inplace = True)
df.reset_index(drop=True, inplace=True)

# filtering for testing
#df = df[df['Provider National Provider Identifier (NPI)'] == 1578814992]
# df['Provider Waiting Room Status EST Event Time'] = df['Provider Waiting Room Status EST Event Time'].dt.tz_localize(None)
# df.to_excel('Outputs/AmWell Log Extracts/peek.xlsx')
# print the first 5 rows of the dataframe
display(df.head(10))
# Get the the first name of the provider usinng provider 
print('5. END OF FIFTH BLOCK'.center(100, '-'))


# In[ ]:


# create dictionary of unique providers
print(df.columns)
provider_ids = df['Provider ID'].value_counts().index.tolist()
providers_dict = {}
display(df[df['Provider ID'] == provider_ids[0]].head(1))
for provider in provider_ids:
    # print all the columns for the first provider
    providers_dict[provider] = {}
    
    providers_dict[provider]['First Name'] = df[df['Provider ID'] == provider]['Provider Waiting Room Status Provider First Name'].iloc[0]
    providers_dict[provider]['Last Name'] = df[df['Provider ID'] == provider]['Provider Waiting Room Status Provider Last Name'].iloc[0]
    # providers_dict[provider]['First Name'] = df[df['Provider ID'] == provider]['Provider First Name'].iloc[0]
    # providers_dict[provider]['Last Name'] = df[df['Provider ID'] == provider]['Provider Last Name'].iloc[0]
    providers_dict[provider]['Provider ID'] = provider
    providers_dict[provider]['NPI'] = df[df['Provider ID'] == provider]['Provider Waiting Room Status Provider NPI'].iloc[0]
# print the first 10 rows of the dictionary
display(pd.DataFrame(providers_dict).T.head(10))
print('6. END OF SIXTH BLOCK'.center(100, '-'))


# In[ ]:


# time functions
def strip_microseconds(delta):
    delta = str(delta)
    try:
        t = dtm.strptime(delta,"%H:%M:%S.%f")
    except:
        t = dtm.strptime(delta,"%H:%M:%S")
    delta = td(hours=t.hour, minutes=t.minute, seconds=t.second)
    return delta

def business_hours(date, start, end):
    time_start = tm(8, 0)
    time_end = tm(20, 0)
    
    start = start.replace(tzinfo=None)
    end = end.replace(tzinfo=None)
    
    business_start = dtm.combine(date, time_start).replace(tzinfo=None)
    business_end = dtm.combine(date, time_end).replace(tzinfo=None)

    if (start > business_start or end < business_end) or (start < business_start and end > business_end):
        #print('bubbled through')
        #print(start, business_start)
        #print(end, business_end)
        
        if end < business_start:
            return td(seconds=0) 
        
        if start > business_end:
            return td(seconds=0)
        
        if start < business_start:
            #print('bubble two')
            start = business_start

        if end > business_end:
            #print('bubble three')
            end = business_end
        return end - start
    else:
        return td(seconds=0)
print('7. END OF SEVENTH BLOCK'.center(100, '-'))


# In[ ]:


#  calculate time logged in and add to providers_dict
# 'Logged In' to 'Logged Out' or 'Disconnected'

for provider in provider_ids:
    
    print(provider)
    
    session_lengths = {}
    start_time = 0
    end_time = 0
    in_flag = 0
    day_lengths = []
    
    # filter for that provider
    provider_df = df[df['Provider ID']==provider]
    
    # extract list of unique dates
    dates = provider_df['Provider Waiting Room Status EST Event Time'].dt.date.value_counts().index.tolist()
    dates.sort()
    #pp.pprint(dates)
    
    # loop through dates and fill up session_lengths
    for i in range(0,len(dates)):
        
        print('new loop date')
        start_date = ''
        end_date = ''
        in_flag = ''
        
        loop_date = dates[i]
        loop_date_before = loop_date - datetime.timedelta(days=1)
        loop_date_after = loop_date + datetime.timedelta(days=1)
        #print(loop_date_before, loop_date, loop_date_after)
        
        # filter df for iterated date plus minus one day
        date_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date]
        date_before_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_before]
        date_after_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_after]
        date_df = pd.concat([date_before_df, date_df, date_after_df])
        date_df.sort_values(by=['Provider Waiting Room Status EST Event Time',
                                'Provider Waiting Room Status Status'], inplace=True)
#         print(provider)
#         display(date_df)
     
        for index, event in date_df.iterrows():

            print('loop date: ' + str(loop_date) + ' ' + 'index: ' + str(index) + ' ' + 'in_flag: ' + str(in_flag) + ' ' + str(event['Provider Waiting Room Status EST Event Time']) + ' ' + str(event['Provider Waiting Room Status Status']))
            quit_flag = 0
            
            # Open window if Logged In
            if 'Logged In' in event['Provider Waiting Room Status Status']:
                in_flag = 1
                start_time = event['Provider Waiting Room Status EST Event Time']
                
            # Close window if Logged Out or Disconnected
            if in_flag == 1 and ('Logged Out' in event['Provider Waiting Room Status Status'] or 'Disconnected' in event['Provider Waiting Room Status Status']):
                in_flag = 0
                end_time = event['Provider Waiting Room Status EST Event Time']
                
                # Create temp dates for logical checks
                tmp_start = start_time.to_pydatetime()
                tmp_end = end_time.to_pydatetime()
                
                print('trying...' + ' ' + str(tmp_start) + ' ' + str(tmp_end))
                
                # if too early or too late then pop out this loop
                if tmp_end.date() < loop_date:
                    quit_flag = 1
                if tmp_start.date() > loop_date:
                    quit_flag = 1
                
                if quit_flag != 1:  
                    
                    print('made it!' + ' ' + str(tmp_start) + ' ' + str(tmp_end))
                    
                    # day boundary cutoffs
                    if tmp_start.date() < loop_date and tmp_end.date() >= loop_date:
                        #print(tmp_start)
                        tmp_start = dtm.combine(loop_date, dtm.min.time())
                        #print(tmp_start)

                    if tmp_end.date() > loop_date and tmp_start.date() <= loop_date:
                        #print(tmp_end)
                        tmp_end = dtm.combine(loop_date, dtm.max.time())
                        #print(tmp_end)                    

                    # Calculate session length
                    session_length = tmp_end.replace(tzinfo=None) - tmp_start.replace(tzinfo=None)
                    session_length = strip_microseconds(session_length)
                    print(session_length)
                    
                    # Update session_lengths dictionary: if date is not already in day_lengths, add it
                    loop_date_str = str(loop_date)
                    if loop_date_str in session_lengths:
                        day_lengths.append(session_length)
                        session_lengths[loop_date_str] = day_lengths
                    else:
                        day_lengths = []
                        day_lengths.append(session_length)
                        session_lengths.update({loop_date_str: day_lengths})
                    
                    pp.pprint(session_lengths)
        
    #pp.pprint(session_lengths)
    providers_dict[provider]['Logged In Deltas by Date'] = session_lengths
print('8. END OF EIGHTH BLOCK'.center(100, '-'))


# In[ ]:


# Calculate time available to see patients and add to providers_dict
# 'Open' or 'On Call' to 'Unavailable', 'Logged Out', or 'Disconnected'

for provider in provider_ids:
    
    print(provider)
    
    session_lengths = {}
    business_lenghts_dict = {}
    moonlight_lenghts_dict = {}
    
    day_lengths = []
    business_lengths = []
    moonlight_lengths = []
    
    start_time = 0
    end_time = 0
    in_flag = 0
    
    daily_start_dict = {}
    daily_end_dict = {}
    
    corrupted = 0
    corrupted_dates = []
    
    # filter events for that provider
    provider_df = df[df['Provider ID']==provider]
    
    # extract list of unique dates
    dates = provider_df['Provider Waiting Room Status EST Event Time'].dt.date.value_counts().index.tolist()
    dates.sort()
    #pp.pprint(dates)
    
    # loop through dates and fill up session_lengths
    for i in range(0,len(dates)):

        first_start = 0

        print('new loop date')
        start_date = ''
        end_date = ''
        in_flag = ''
                
        loop_date = dates[i]
        loop_date_before = loop_date - datetime.timedelta(days=1)
        loop_date_after = loop_date + datetime.timedelta(days=1)
        #print(loop_date_before, loop_date, loop_date_after)
        
        # filter df for iterated date plus minus one day
        date_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date]
        date_before_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_before]
        date_after_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_after]
        date_df = pd.concat([date_df, date_before_df])
        date_df = pd.concat([date_df, date_after_df])
        date_df.sort_values(by=['Provider Waiting Room Status EST Event Time',
                                'Provider Waiting Room Status Status'], inplace=True)
        #display(date_df)
     
        for index, event in date_df.iterrows():

            print('loop date: ' + str(loop_date) + ' ' + 'index: ' + str(index) + ' ' + 'in_flag: ' + str(in_flag) + ' ' + str(event['Provider Waiting Room Status EST Event Time']) + ' ' + str(event['Provider Waiting Room Status Status']))
            quit_flag = 0
            
            # Open window if Open
            if 'Open' in event['Provider Waiting Room Status Status'] or 'On Call' in event['Provider Waiting Room Status Status']:
                in_flag = 1
                start_time = event['Provider Waiting Room Status EST Event Time']
            
            # Close window if Unavailable, Disconnected, or Logged Out
            if in_flag == 1 and ('Unavailable' in event['Provider Waiting Room Status Status'] or 'Disconnected' in event['Provider Waiting Room Status Status'] or 'Logged Out' in event['Provider Waiting Room Status Status']):     
                in_flag = 0
                end_time = event['Provider Waiting Room Status EST Event Time']
                                
                # Create temp dates for logical checks
                tmp_start = start_time.to_pydatetime()
                tmp_end = end_time.to_pydatetime()
                
                print('trying...' + ' ' + str(tmp_start) + ' ' + str(tmp_end))
                
                # if too early or too late then pop out this loop
                if tmp_end.date() < loop_date:
                    quit_flag = 1
                if tmp_start.date() > loop_date:
                    quit_flag = 1
                
                if quit_flag != 1: 
                
                    print('made it!' + ' ' + str(tmp_start) + ' ' + str(tmp_end))
                    
                    # day boundary cutoffs
                    if tmp_start.date() < loop_date and tmp_end.date() >= loop_date:
                        #print(tmp_start)
                        tmp_start = dtm.combine(loop_date, dtm.min.time())
                        #print(tmp_start)

                    if tmp_end.date() > loop_date and tmp_start.date() <= loop_date:
                        #print(tmp_end)
                        tmp_end = dtm.combine(loop_date, dtm.max.time())
                        #print(tmp_end)                    

                    # Calculate session length
                    session_length = tmp_end.replace(tzinfo=None) - tmp_start.replace(tzinfo=None)
                    session_length = strip_microseconds(session_length)
                    print(session_length)
                    
                    # Update session_lengths dictionary: if date is not already in day_lengths, add it
                    loop_date_str = str(loop_date)
                    if loop_date_str in session_lengths:
                        print('already there')
                        day_lengths.append(session_length)
                        session_lengths[loop_date_str] = day_lengths
                    else:
                        print('adding new day')
                        day_lengths = []
                        day_lengths.append(session_length)
                        session_lengths.update({loop_date_str: day_lengths})
                        
                    # add daily start and end times
                    if first_start == 0:
                        first_start = 1
                        daily_start_dict[loop_date_str] = tmp_start
                    daily_end_dict[loop_date_str] = tmp_end
                        
                    # Calculate Business and Moonlight Hours: 
                    business_time = business_hours(loop_date, tmp_start, tmp_end)
                    business_time = strip_microseconds(business_time)
                    moonlight_time = session_length - business_time
                    
                    # Update business_lenghts_dict dictionary
                    loop_date_str = str(loop_date)
                    if loop_date_str in business_lenghts_dict:
                        business_lengths.append(business_time)
                        business_lenghts_dict[loop_date_str] = business_lengths
                    else:
                        business_lengths = []
                        business_lengths.append(business_time)
                        business_lenghts_dict.update({loop_date_str: business_lengths})
                        
                    # Update moonlight_lenghts_dict dictionary
                    loop_date_str = str(loop_date)
                    if loop_date_str in moonlight_lenghts_dict:
                        moonlight_lengths.append(moonlight_time)
                        moonlight_lenghts_dict[loop_date_str] = moonlight_lengths
                    else:
                        moonlight_lengths = []
                        moonlight_lengths.append(moonlight_time)
                        moonlight_lenghts_dict.update({loop_date_str: moonlight_lengths})    
                    
                    #print(tmp_start, tmp_end, session_length, business_time, moonlight_time)
        #print("day end")
        
    #pp.pprint(session_lengths)
    providers_dict[provider]['Available Deltas by Date'] = session_lengths
    providers_dict[provider]['Business Deltas by Date'] = business_lenghts_dict
    providers_dict[provider]['Moonlight Deltas by Date'] = moonlight_lenghts_dict
    providers_dict[provider]['Available_Corrupted Dates'] = corrupted_dates
    providers_dict[provider]['Daily Start'] = daily_start_dict
    providers_dict[provider]['Daily End'] = daily_end_dict
print('9. END OF NINTH BLOCK'.center(100, '-'))


# In[ ]:


pp.pprint(providers_dict)
print('10. END OF TENTH BLOCK'.center(100, '-'))


# In[ ]:


# transform providers_dict to format for output

output = {}
index = 0

for provider in providers_dict:
    
    logged_in_dates = list(providers_dict[provider]['Logged In Deltas by Date'].keys())
    available_dates = list(providers_dict[provider]['Available Deltas by Date'].keys())
    dates = list(set(logged_in_dates) | set(available_dates)) 
        
    for date in dates:
        
        # Set basic information
        output[index] = {}
        output[index]['First Name'] = providers_dict[provider]['First Name']
        output[index]['Last Name'] = providers_dict[provider]['Last Name']
        output[index]['Provider ID'] = providers_dict[provider]['Provider ID']
        output[index]['NPI'] = providers_dict[provider]['NPI']
        output[index]['Date'] = date
        
        # add logged in times
        try:
            output[index]['Number of Logged In Sessions'] = len(providers_dict[provider]['Logged In Deltas by Date'][date])
        except:
            output[index]['Number of Logged In Sessions'] = 'error'
        try:
            output[index]['Total Time Logged In'] = str(sum(providers_dict[provider]['Logged In Deltas by Date'][date], datetime.timedelta()))[-9:].lstrip()
        except:
            output[index]['Total Time Logged In'] = 'error'
        
        # add available times
        try:
            output[index]['Number of Available Sessions'] = len(providers_dict[provider]['Available Deltas by Date'][date])
        except:
            output[index]['Number of Available Sessions'] = ''
        try:
            output[index]['Total Time Available'] = str(sum(providers_dict[provider]['Available Deltas by Date'][date], datetime.timedelta()))[-9:].lstrip()
        except:
            output[index]['Total Time Available'] = ''
        try:
            output[index]['Total Time Available (seconds)'] = str(sum(providers_dict[provider]['Available Deltas by Date'][date], datetime.timedelta()).total_seconds())
        except:
            output[index]['Total Time Available (seconds)'] = ''
        try:
            output[index]['Daily Start Timestamp'] = str(providers_dict[provider]['Daily Start'][date])[11:-6]
        except:
            output[index]['Daily Start Timestamp'] = ''
        try:
            output[index]['Daily End Timestamp'] = str(providers_dict[provider]['Daily End'][date])[11:-6]
        except:
            output[index]['Daily End Timestamp'] = ''            
        
        # add business/moonlight times
        try:
            output[index]['Business Hours'] = str(sum(providers_dict[provider]['Business Deltas by Date'][date], datetime.timedelta()))[-9:]
        except:
            output[index]['Business Hours'] = ''
        try:
            output[index]['Moonlight Hours'] = str(sum(providers_dict[provider]['Moonlight Deltas by Date'][date], datetime.timedelta()))[-9:]
        except:
            output[index]['Moonlight Hours'] = ''
            
        index += 1

pp.pprint(output)
print('11. END OF TENTH BLOCK'.center(100, '-'))


# In[ ]:


# create and format final data frame from dictionary
df_final = pd.DataFrame.from_dict(output, orient = 'index')
# print the first 60 rows of the final data frame
df_final.head(20)

df_final["Name"] = df_final["First Name"] +" "+ df_final["Last Name"]
pp.pprint(df_final.columns)
pp.pprint(df_final.head(20))



df_final = df_final[['Date', 'NPI', 'Provider ID', 'Name',
                    'Total Time Logged In', 'Total Time Available', 'Total Time Available (seconds)',
                    'Daily Start Timestamp','Daily End Timestamp','Business Hours', 'Moonlight Hours']]
print('12. END OF ELEVENTH BLOCK'.center(100, '-'))


# In[ ]:


# Define the output file path
output_file = 'output2.xlsx'
root_billing_folder = '/Users/aman/dev-repositories/amwell-automation'
output_path = f'{root_billing_folder}/{output_file}'

# Drop unnecessary columns
columns_to_drop = ['Daily Start Timestamp', 'Daily End Timestamp']
df_final = df_final.drop(columns=columns_to_drop)

# Convert the first column to datetime format if not already, and format it to date-only string
df_final.iloc[:, 0] = pd.to_datetime(df_final.iloc[:, 0], errors='coerce').dt.date

# Sort the DataFrame by the first column
df_final = df_final.sort_values(by=df_final.columns[0])

# Save the DataFrame to an Excel file, without including the DataFrame's index
df_final.to_excel(output_path, index=False)
print('13. END OF ELEVENTH BLOCK'.center(100, '-'))

