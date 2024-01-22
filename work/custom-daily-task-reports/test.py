import pandas as pd
import numpy as np  # To install: pip install numpy
import matplotlib.pyplot as plt

import logging
from datetime import datetime
import sys

# Setting up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
selected_task = None
lines = []


def read_data(file_path):
    """
    Reads data from CSV file.
    Args:
        file_path (str): Path to the CSV file.
    Returns:
        DataFrame: Pandas DataFrame containing the data.
    """
    try:
        data = pd.read_csv(file_path)
        logging.info("Data read successfully from {}".format(file_path))

        # Print out unique values in 'Start Date' column
        # print("Unique values in 'Start Date':", data['Start Date'].unique())

        return data
    except FileNotFoundError:
        logging.error("File not found: {}".format(file_path))
        sys.exit("File not found, please check the file path.")
    except Exception as e:
        logging.error("Error reading file: {}".format(e))
        sys.exit("Error occurred while reading the file.")


def process_data(data, exclude_tasks=None, group_tasks=None):
    """
    Processes the data to find the start week of tasks and count occurrences.
    Args:
        data (DataFrame): Pandas DataFrame of the task data.
        exclude_tasks (list): List of task types to exclude.
        group_tasks (dict): Dictionary mapping new task names to lists of task types to be grouped.
    Returns:
        DataFrame: Processed data with counts of tasks starting each week.
    """
    try:
        # Remove rows with empty 'Start Date'
        data = data.dropna(subset=['Start Date'])

        # Filter out excluded tasks if specified
        if exclude_tasks:
            data = data[~data['Task Type'].isin(exclude_tasks)]

        # Group similar tasks if specified
        if group_tasks:
            for new_name, task_list in group_tasks.items():
                data['Task Type'] = data['Task Type'].replace(
                    task_list, new_name)

        # Convert 'Start Date' to datetime, assuming the format 'MM/DD/YYYY'
        data['Start Date'] = pd.to_datetime(
            data['Start Date'], format='%m/%d/%Y', errors='coerce')

        # Check for any NaT (Not a Time) values which indicate parsing errors
        if data['Start Date'].isnull().any():
            # Log the rows with NaT values before removing them
            nat_rows = data[data['Start Date'].isnull()]
            logging.warning(
                "Rows with unparseable 'Start Date' will be ignored:\n{}".format(nat_rows))

            # Remove rows with NaT values
            data = data.dropna(subset=['Start Date'])

        # Ensure there's no attempt to process an empty dataframe
        if data.empty:
            logging.error(
                "No data available after removing rows with invalid 'Start Date'.")
            sys.exit("Exiting: No data to process after cleaning.")

        # Determine the start of the week (Sunday)
        data['Week Start'] = data['Start Date'].apply(
            lambda x: x - pd.Timedelta(days=x.dayofweek))

        # Group by week and task type, then count occurrences
        weekly_data = data.groupby(
            ['Week Start', 'Task Type']).size().reset_index(name='Counts')
        logging.info("Data processing completed successfully")
        return weekly_data
    except Exception as e:
        logging.error("Error processing data: {}".format(e))
        sys.exit("Error occurred while processing the data.")


def filter_data_for_quarter(data, start_month, end_month, year):
    """
    Filters the data for a specific fiscal quarter.
    Args:
        data (DataFrame): Processed data with weekly task counts.
        start_month (int): Starting month of the quarter.
        end_month (int): Ending month of the quarter.
        year (int): Year of the quarter.
    Returns:
        DataFrame: Data filtered for the specific quarter.
    """
    start_date = datetime(year, start_month, 1)
    end_date = datetime(year, end_month, 30)
    return data[(data['Week Start'] >= start_date) & (data['Week Start'] <= end_date)]


def on_legend_click(event):
    """Handles click events on the legend."""
    global selected_task, lines
    legend_text = event.artist.get_text().split(" (")[0]

    if selected_task == legend_text:
        # Clear selection if the same task type is clicked again
        selected_task = None
        for line in lines:
            line.set_alpha(1.0)  # Restore original color
    else:
        selected_task = legend_text
        for line in lines:
            # Blur out other task types
            alpha_value = 0.1 if not line.get_label().startswith(legend_text) else 1.0
            line.set_alpha(alpha_value)

    plt.draw()


def plot_data(data, title, start_month, end_month, year):
    # global lines
    # lines = []

    # Plotting
    plt.figure(figsize=(12, 6))

    # Sum the task counts for each task type and sort them in descending order
    task_counts = data.groupby('Task Type')[
        'Counts'].sum().sort_values(ascending=False)

    # Define a color map for each task type using the updated method
    color_dict = dict(
        zip(task_counts.index, plt.cm.tab20.colors[:len(task_counts)]))

    # Generate all week start dates within the range
    start_date = datetime(year, start_month, 1)
    end_date = datetime(year, end_month, 30)
    week_starts = pd.date_range(start_date, end_date, freq='W-SUN')

    # Plot each task type using the sorted order and assigned colors
    for task in task_counts.index:
        task_data = data[data['Task Type'] == task]
        line, = plt.plot(task_data['Week Start'], task_data['Counts'], marker='o',
                         label=f"{task} ({task_counts[task]})", color=color_dict[task])
        lines.append(line)

    # Adjust y-axis intervals and add horizontal lines
    max_count = data['Counts'].max()
    # Adjust this step for different intervals
    yticks = range(0, max_count + 5, 5)
    plt.yticks(yticks)
    for y in yticks:
        plt.axhline(y=y, color='gray', linestyle='--',
                    linewidth=0.5, alpha=0.5)

    # Draw a vertical line for each week start
    for date in week_starts:
        plt.axvline(x=date, color='gray', linestyle='--',
                    linewidth=0.5, alpha=0.5)

    plt.title(title)
    plt.xlabel('Week Start Date')
    plt.ylabel('Task Count')
    plt.xticks(week_starts, rotation=45)

    # Improving legend visuals
    legend = plt.legend(title='Task Types (Total Counts)',
                        bbox_to_anchor=(1.05, 1), loc='upper left')

    # Make the plot interactive
    plt.gcf().canvas.mpl_connect('pick_event', on_legend_click)
    for text in legend.get_texts():
        text.set_picker(True)  # Enable picking on each legend text

    plt.tight_layout(rect=[0, 0, 0.85, 1])


def main():
    """
    Main function to run the script.
    """
    # Define tasks to exclude and groups
    exclude_tasks = ['PTO', 'Development', 'Official Holiday']
    group_tasks = {
        'Content Review': ['Content Review QA1', 'Content Review QA2', 'Content Review QA3', 'Content Review QA4', 'Content Review QA5', 'Content Review QA6', 'Content Review QA7', 'Content Review QA8', 'Content Review QA9', 'Content Review QA10'],
        'Testing': ['Ticket Testing', 'Testing'],
        'Created Ticket': ['Created Ticket', 'Created Jira Ticket'],
        'Research': ['Research', 'Verify', 'Discovery'],
        'Meeting': ['Meeting', 'Meeting | In-Person', 'Meeting | Hybrid'],
        'Proofreading': ['Proofreading %231', 'Proofreading %232']
    }

    # Read data
    file_path = 'test.csv'
    data = read_data(file_path)

    # Process data with filtering and grouping
    processed_data = process_data(
        data, exclude_tasks=exclude_tasks, group_tasks=group_tasks)

    # Filter data for each quarter and plot
    for quarter, (start_month, end_month, year) in {
        # 'Q4 FY 2023': (4, 6, 2023),
        # 'Q1 FY 2024': (7, 9, 2023),
        'Q2 FY 2024': (10, 12, 2023)
    }.items():
        quarter_data = filter_data_for_quarter(
            processed_data, start_month, end_month, year)
    plot_data(quarter_data, quarter, start_month, end_month, year)

    plt.show()


if __name__ == "__main__":
    main()
