#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd
import logging
import datetime
from datetime import datetime as dtm
from datetime import time as tm
from datetime import timedelta as td

# Uncommenting the following line will display all columns in the dataframe
# pd.set_option('display.max_colwidth', None)

# Clear the log file if it exists
# Log file name: today's date + script.log
today = datetime.datetime.now().strftime("%Y-%m-%d")
log_file_name = today + '_script.log'

# create a directory for the logs if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# remove the log file if it exists in the logs directory
if os.path.exists(os.path.join('logs', log_file_name)):
    os.remove(os.path.join('logs', log_file_name))

# create the log file in the logs directory
logging.basicConfig(filename=os.path.join('logs', log_file_name),
                    level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p')


def setup_environment(root_billing_folder: str):
    """Sets the working directory to the given path."""
    try:
        os.chdir(root_billing_folder)
        logging.info(
            f"Function Name: setup_environment | Changed directory to {root_billing_folder}".center(100, "-"))
    except Exception as e:
        logging.error(
            f"Failed to change directory to {root_billing_folder}. Error: {e}".center(100, "-"))


def load_data(downloaded_file: str, provider_file: str) -> (pd.DataFrame, pd.DataFrame):
    """Loads and returns the hours and providers dataframes."""
    try:
        hours = pd.read_excel(downloaded_file)
        providers = pd.read_excel(provider_file)
        logging.info(
            f"Function Name: load_data | Data loaded successfully from {downloaded_file} and {provider_file}".center(100, "-"))
        return hours, providers
    except Exception as e:
        logging.error(f"Error in loading data. {e}")


def process_data(hours: pd.DataFrame, providers: pd.DataFrame) -> pd.DataFrame:
    """Processes the given dataframes and returns the modified dataframe."""
    try:
        # By using a left join, we are not filtering out any data from the hours dataframe
        df = hours.set_index('Provider Waiting Room Status Provider ID').join(
            providers.set_index('Provider ID'), how='left')

        df.reset_index(level=0, inplace=True)
        df.rename(columns={
                  'Provider Waiting Room Status Provider ID': 'Provider ID'}, inplace=True)
        df.drop_duplicates(['Provider Waiting Room Status UTC Event Time',
                            'Provider Waiting Room Status Status', 'Provider ID'], keep='last', inplace=True)
        df = df[df['Provider Waiting Room Status Status'].notna()]
        # First 10 rows of the dataframe
        log_output = df.head(10)
        logging.info("-"*100)
        logging.info(
            f"Function Name: process_data | Data processed successfully. First 10 rows of the dataframe: \n {log_output}")
        return df
    except Exception as e:
        logging.error(f"Error in processing data. {e}")


def set_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """Sets datetime as index and creates EST column, then sorts by time."""
    try:
        pd.to_datetime(df['Provider Waiting Room Status UTC Event Time'])
        df = df.set_index('Provider Waiting Room Status UTC Event Time')
        df['Provider Waiting Room Status EST Event Time'] = df.index.tz_localize(
            'UTC').tz_convert('US/Eastern')
        df['Provider Waiting Room Status EST Event Time'] = pd.to_datetime(
            df['Provider Waiting Room Status EST Event Time'])
        df.sort_index(inplace=True)
        df.reset_index(inplace=True, drop=True)
        logging.info(
            f"Function Name: set_datetime_index | Datetime index set successfully.".center(100, "-"))
        return df
    except Exception as e:
        logging.error(f"Error in setting datetime index. {e}")


def categorize_waiting_room_status(df: pd.DataFrame) -> pd.DataFrame:
    """Categorizes waiting room status."""
    try:
        df['Provider Waiting Room Status Status'] = pd.Categorical(
            df['Provider Waiting Room Status Status'],
            ["Login Status - Disconnected", "Login Status - Logged Out",
             "Login Status - Logged In", "Waiting Room - Unavailable",
             "Waiting Room - Open", "Waiting Room - On Call",
             "Waiting Room - Ask Me"])
        logging.info(
            f"Function Name: categorize_waiting_room_status | Waiting room status categorized successfully.".center(100, "-"))
        return df
    except Exception as e:
        logging.error(f"Error in categorizing waiting room status. {e}")


def create_provider_dictionary(df: pd.DataFrame) -> dict:
    """Creates a dictionary of unique providers."""
    try:
        provider_ids = df['Provider ID'].value_counts().index.tolist()
        providers_dict = {}
        for provider in provider_ids:
            providers_dict[provider] = {
                'First Name': df[df['Provider ID'] == provider]['Provider Waiting Room Status Provider First Name'].iloc[0],
                'Last Name': df[df['Provider ID'] == provider]['Provider Waiting Room Status Provider Last Name'].iloc[0],
                'Provider ID': provider,
                'NPI': df[df['Provider ID'] == provider]['Provider Waiting Room Status Provider NPI'].iloc[0]
            }
        # first 10 rows of the dictionary
        log_output = pd.DataFrame.from_dict(
            providers_dict, orient='index').head(10)
        logging.info("-"*100)
        logging.info(
            f"Function Name: create_provider_dictionary | Provider dictionary created successfully. First 10 rows of the dictionary: \n {log_output}")
        return providers_dict
    except Exception as e:
        logging.error(f"Error in creating provider dictionary. {e}")


def sort_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sorts the dataframe by specified columns."""
    try:
        df.sort_values(by=['Provider National Provider Identifier (NPI)',
                           'Provider Waiting Room Status EST Event Time',
                           'Provider Waiting Room Status Status'], inplace=True)
        df.reset_index(drop=True, inplace=True)
        logging.info(
            f"Function Name: sort_dataframe | Dataframe sorted successfully.".center(100, "-"))
        return df
    except Exception as e:
        logging.error(f"Error in sorting dataframe. {e}")


def strip_microseconds(delta):
    delta = str(delta)
    try:
        t = dtm.strptime(delta, "%H:%M:%S.%f")
    except:
        t = dtm.strptime(delta, "%H:%M:%S")
    delta = td(hours=t.hour, minutes=t.minute, seconds=t.second)
    return delta


def get_session_lengths(df, provider_ids, providers_dict):
    for provider in provider_ids:

        session_lengths = {}
        start_time = 0
        end_time = 0
        in_flag = 0
        day_lengths = []
        provider_df = df[df['Provider ID'] == provider]
        dates = provider_df['Provider Waiting Room Status EST Event Time'].dt.date.value_counts(
        ).index.tolist()
        dates.sort()
        for i in range(0, len(dates)):

            start_date = ''
            end_date = ''
            in_flag = ''
            loop_date = dates[i]
            loop_date_before = loop_date - datetime.timedelta(days=1)
            loop_date_after = loop_date + datetime.timedelta(days=1)
            date_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date]
            date_before_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_before]
            date_after_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_after]
            date_df = pd.concat([date_before_df, date_df, date_after_df])
            date_df.sort_values(by=['Provider Waiting Room Status EST Event Time',
                                    'Provider Waiting Room Status Status'], inplace=True)
            for index, event in date_df.iterrows():

                quit_flag = 0
                if 'Logged In' in event['Provider Waiting Room Status Status']:
                    in_flag = 1
                    start_time = event['Provider Waiting Room Status EST Event Time']
                if in_flag == 1 and ('Logged Out' in event['Provider Waiting Room Status Status'] or 'Disconnected' in event['Provider Waiting Room Status Status']):
                    in_flag = 0
                    end_time = event['Provider Waiting Room Status EST Event Time']
                    tmp_start = start_time.to_pydatetime()
                    tmp_end = end_time.to_pydatetime()

                    if tmp_end.date() < loop_date:
                        quit_flag = 1
                    if tmp_start.date() > loop_date:
                        quit_flag = 1
                    if quit_flag != 1:
                        if tmp_start.date() < loop_date and tmp_end.date() >= loop_date:
                            tmp_start = dtm.combine(loop_date, dtm.min.time())
                        if tmp_end.date() > loop_date and tmp_start.date() <= loop_date:
                            tmp_end = dtm.combine(loop_date, dtm.max.time())
                        session_length = tmp_end.replace(
                            tzinfo=None) - tmp_start.replace(tzinfo=None)
                        session_length = strip_microseconds(session_length)

                        loop_date_str = str(loop_date)
                        if loop_date_str in session_lengths:
                            day_lengths.append(session_length)
                            session_lengths[loop_date_str] = day_lengths
                        else:
                            day_lengths = []
                            day_lengths.append(session_length)
                            session_lengths.update(
                                {loop_date_str: day_lengths})
        providers_dict[provider]['Logged In Deltas by Date'] = session_lengths
    # Log the providers dictionary, only the first 10 rows
    log_output = pd.DataFrame.from_dict(
        providers_dict, orient='index').head(10)
    logging.info("-"*100)
    logging.info(
        f"Function Name: get_session_lengths | Providers dictionary first 10 rows: \n {log_output}")

    return providers_dict


def calculate_deltas(df, provider_ids, providers_dict):

    def business_hours(date, start, end):
        time_start = tm(8, 0)
        time_end = tm(20, 0)
        start = start.replace(tzinfo=None)
        end = end.replace(tzinfo=None)
        business_start = dtm.combine(date, time_start).replace(tzinfo=None)
        business_end = dtm.combine(date, time_end).replace(tzinfo=None)
        if (start > business_start or end < business_end) or (start < business_start and end > business_end):
            if end < business_start:
                return td(seconds=0)
            if start > business_end:
                return td(seconds=0)
            if start < business_start:
                start = business_start
            if end > business_end:
                end = business_end
            return end - start
        else:
            return td(seconds=0)

    # Calculate time available to see patients and add to providers_dict
    # 'Open' or 'On Call' to 'Unavailable', 'Logged Out', or 'Disconnected'
    for provider in provider_ids:

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
        provider_df = df[df['Provider ID'] == provider]

        # extract list of unique dates
        dates = provider_df['Provider Waiting Room Status EST Event Time'].dt.date.value_counts(
        ).index.tolist()
        dates.sort()

        # loop through dates and fill up session_lengths
        for i in range(0, len(dates)):

            first_start = 0
            loop_date = dates[i]
            loop_date_before = loop_date - datetime.timedelta(days=1)
            loop_date_after = loop_date + datetime.timedelta(days=1)

            # filter df for iterated date plus minus one day
            date_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date]
            date_before_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_before]
            date_after_df = provider_df[provider_df['Provider Waiting Room Status EST Event Time'].dt.date == loop_date_after]
            date_df = pd.concat([date_df, date_before_df])
            date_df = pd.concat([date_df, date_after_df])
            date_df.sort_values(by=['Provider Waiting Room Status EST Event Time',
                                    'Provider Waiting Room Status Status'], inplace=True)

            for index, event in date_df.iterrows():

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

                    # if too early or too late then pop out this loop
                    if tmp_end.date() < loop_date:
                        quit_flag = 1
                    if tmp_start.date() > loop_date:
                        quit_flag = 1

                    if quit_flag != 1:

                        # day boundary cutoffs
                        if tmp_start.date() < loop_date and tmp_end.date() >= loop_date:
                            tmp_start = dtm.combine(loop_date, dtm.min.time())

                        if tmp_end.date() > loop_date and tmp_start.date() <= loop_date:
                            tmp_end = dtm.combine(loop_date, dtm.max.time())

                        # Calculate session length
                        session_length = tmp_end.replace(
                            tzinfo=None) - tmp_start.replace(tzinfo=None)
                        session_length = strip_microseconds(session_length)

                        # Update session_lengths dictionary: if date is not already in day_lengths, add it
                        loop_date_str = str(loop_date)
                        if loop_date_str in session_lengths:
                            day_lengths.append(session_length)
                            session_lengths[loop_date_str] = day_lengths
                        else:
                            day_lengths = []
                            day_lengths.append(session_length)
                            session_lengths.update(
                                {loop_date_str: day_lengths})

                        # add daily start and end times
                        if first_start == 0:
                            first_start = 1
                            daily_start_dict[loop_date_str] = tmp_start
                        daily_end_dict[loop_date_str] = tmp_end

                        # Calculate Business and Moonlight Hours:
                        business_time = business_hours(
                            loop_date, tmp_start, tmp_end)
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
                            business_lenghts_dict.update(
                                {loop_date_str: business_lengths})

                        # Update moonlight_lenghts_dict dictionary
                        loop_date_str = str(loop_date)
                        if loop_date_str in moonlight_lenghts_dict:
                            moonlight_lengths.append(moonlight_time)
                            moonlight_lenghts_dict[loop_date_str] = moonlight_lengths
                        else:
                            moonlight_lengths = []
                            moonlight_lengths.append(moonlight_time)
                            moonlight_lenghts_dict.update(
                                {loop_date_str: moonlight_lengths})

        providers_dict[provider]['Available Deltas by Date'] = session_lengths
        providers_dict[provider]['Business Deltas by Date'] = business_lenghts_dict
        providers_dict[provider]['Moonlight Deltas by Date'] = moonlight_lenghts_dict
        providers_dict[provider]['Available_Corrupted Dates'] = corrupted_dates
        providers_dict[provider]['Daily Start'] = daily_start_dict
        providers_dict[provider]['Daily End'] = daily_end_dict

    log_output = pd.DataFrame.from_dict(
        providers_dict, orient='index').head(10)
    logging.info("-"*100)
    logging.info(
        f"Function Name: calculate_deltas | Providers dictionary first 10 rows: \n {log_output}")

    return providers_dict


def transform_data_to_output_format(providers_dict):
    output = {}
    index = 0

    for provider in providers_dict:

        logged_in_dates = list(providers_dict[provider].get(
            'Logged In Deltas by Date', {}).keys())
        available_dates = list(providers_dict[provider].get(
            'Available Deltas by Date', {}).keys())
        dates = list(set(logged_in_dates) | set(available_dates))

        for date in dates:
            # Initialize dictionary for the current index
            output[index] = {}

            # Set basic information
            output[index]['First Name'] = providers_dict[provider].get(
                'First Name', '')
            output[index]['Last Name'] = providers_dict[provider].get(
                'Last Name', '')
            output[index]['Provider ID'] = providers_dict[provider].get(
                'Provider ID', '')
            output[index]['NPI'] = providers_dict[provider].get('NPI', '')
            output[index]['Date'] = date

            # Add logged in times
            try:
                output[index]['Number of Logged In Sessions'] = len(
                    providers_dict[provider]['Logged In Deltas by Date'][date])
            except:
                output[index]['Number of Logged In Sessions'] = 'error'
            try:
                output[index]['Total Time Logged In'] = str(sum(
                    providers_dict[provider]['Logged In Deltas by Date'][date], datetime.timedelta()))[-9:].lstrip()
            except:
                output[index]['Total Time Logged In'] = 'error'

            # Add available times
            try:
                output[index]['Number of Available Sessions'] = len(
                    providers_dict[provider]['Available Deltas by Date'][date])
            except:
                output[index]['Number of Available Sessions'] = ''
            try:
                output[index]['Total Time Available'] = str(sum(
                    providers_dict[provider]['Available Deltas by Date'][date], datetime.timedelta()))[-9:].lstrip()
            except:
                output[index]['Total Time Available'] = ''
            try:
                output[index]['Total Time Available (seconds)'] = str(sum(
                    providers_dict[provider]['Available Deltas by Date'][date], datetime.timedelta()).total_seconds())
            except:
                output[index]['Total Time Available (seconds)'] = ''
            try:
                output[index]['Daily Start Timestamp'] = str(
                    providers_dict[provider]['Daily Start'][date])[11:-6]
            except:
                output[index]['Daily Start Timestamp'] = ''
            try:
                output[index]['Daily End Timestamp'] = str(
                    providers_dict[provider]['Daily End'][date])[11:-6]
            except:
                output[index]['Daily End Timestamp'] = ''

            # Add business/moonlight times
            try:
                output[index]['Business Hours'] = str(sum(
                    providers_dict[provider]['Business Deltas by Date'][date], datetime.timedelta()))[-9:].lstrip()
            except:
                output[index]['Business Hours'] = ''
            try:
                output[index]['Moonlight Hours'] = str(sum(
                    providers_dict[provider]['Moonlight Deltas by Date'][date], datetime.timedelta()))[-9:].lstrip()
            except:
                output[index]['Moonlight Hours'] = ''

            index += 1

    log_output = pd.DataFrame.from_dict(output, orient='index').head(10)
    logging.info("-"*100)
    logging.info(
        f"Function Name: transform_data_to_output_format | Output dictionary first 10 rows: \n {log_output}")
    return output


def create_dataframe_from_output(output):
    # Print the output dictionary
    print("DIC RETURNED | CREATE DATAFRAME".center(100, "-"))
    print(pd.DataFrame.from_dict(output, orient='index'))
    df = pd.DataFrame.from_dict(output, orient='index')
    df["Name"] = df["First Name"] + " " + df["Last Name"]
    desired_cols = ['Date', 'NPI', 'Provider ID', 'Name', 'Total Time Logged In',
                    'Total Time Available', 'Total Time Available (seconds)', 'Daily Start Timestamp',
                    'Daily End Timestamp', 'Business Hours', 'Moonlight Hours']
    df = df[desired_cols]

    # TODO | Properly configure this later but for now remove Daily Start Timestamp and Daily End Timestamp
    df.drop(columns=['Daily Start Timestamp', 'Daily End Timestamp'],
            inplace=True)
    # Before sending to excel, sort by date and then by name
    df.sort_values(by=['Date', 'Name'], inplace=True)

    log_output = df.head(10)
    logging.info("-"*100)
    logging.info(
        f"Function Name: create_dataframe_from_output | DataFrame first 10 rows: \n {log_output}")
    return df


def save_dataframe_to_excel(df, path):
    try:
        df.to_excel(path)
        # Remove the index column
        df.to_excel(path, index=False)
        logging.info(
            f"Function Name: save_dataframe_to_excel | DataFrame saved successfully to {path}".center(100, "-"))
    except Exception as e:
        logging.error(f"Error saving DataFrame to path {path}. Error: {e}")


if __name__ == '__main__':
    root_billing_folder = '/Users/aman-mac-work/dev/amwell-automation'
    provider_file = 'providers.xlsx'
    downloaded_file = 'test.xlsx'
    output_path = 'NEW_SCRIPT_OUTPUT.xlsx'

    setup_environment(root_billing_folder)
    hours, providers = load_data(downloaded_file, provider_file)
    # This is where the filtering happens, but currently it is not filtering anything out because of the left join
    df = process_data(hours, providers)
    df = set_datetime_index(df)
    df = categorize_waiting_room_status(df)
    df = sort_dataframe(df)

    providers_dict = create_provider_dictionary(df)
    providers_dict = get_session_lengths(
        df, providers_dict.keys(), providers_dict)
    providers_dict = calculate_deltas(
        df, providers_dict.keys(), providers_dict)
    output_data = transform_data_to_output_format(providers_dict)
    df_final = create_dataframe_from_output(output_data)
    save_dataframe_to_excel(df_final, output_path)
    logging.info(
        f"Function Name: __main__ | Script completed successfully.".center(100, "-"))
