import pandas as pd
import json
from datetime import datetime


def parse_log_line(line):
    """Parse a single line of the log file."""
    parts = line.split(' ', 2)
    process_time = parts[0]
    log_level = parts[1]
    log_message = json.loads(parts[2])['message']

    # Convert process time to 'yyyy/mm/dd hh:mm:ss' format
    process_time_formatted = datetime.now().strftime('%Y/%m/%d ') + process_time
    return process_time_formatted, log_level, log_message


def process_log_file(file_path):
    """Process the log file and save to Excel."""
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            data.append(parse_log_line(line))

    # Create a DataFrame
    df = pd.DataFrame(
        data, columns=['Process Time', 'Log Level', 'Log Message'])

    # Write to Excel
    excel_path = 'output_' + datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + '.xlsx'
    df.to_excel(excel_path, index=False)


# Replace 'path_to_log_file.log' with the actual path of your log file
process_log_file(
    '/Users/aman-mac-work/scripts/work/coe-uipath/uipath-log-parser/uipath-log-files/2023-12-01_Execution.log')

# Example script execution:
# python3 uipath-log-parser.py
