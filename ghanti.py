from datetime import datetime, timedelta
import os

def parse_event_line(line):
    parts = line.strip().split(',')
    event_type = int(parts[0])
    
    if event_type in (1, 2):  # Mid-semester or End-semester
        slot = int(parts[1])
        start_date = datetime.strptime(parts[2], "%d-%m-%Y")
        
        if len(parts) > 4:  # If there are 5 parts, it means there's a date range and a time
            end_date = datetime.strptime(parts[3], "%d-%m-%Y")
            event_time = datetime.strptime(parts[4], "%H:%M:%S").time()
        elif len(parts) > 3:  # If there are 4 parts, it could be either end date or time
            try:
                end_date = datetime.strptime(parts[3], "%d-%m-%Y")
                event_time = None
            except ValueError:  # If it fails to parse as a date, it must be a time
                end_date = start_date
                event_time = datetime.strptime(parts[3], "%H:%M:%S").time()
        else:  # Only 3 parts, no end date or time
            end_date = start_date
            event_time = None
        
        return event_type, slot, start_date, end_date, event_time
    
    else:  # Holiday
        start_date = datetime.strptime(parts[1], "%d-%m-%Y")
        end_date = datetime.strptime(parts[2], "%d-%m-%Y") if len(parts) > 2 else start_date
        return event_type, None, start_date, end_date, None

def read_and_process_events(input_file):
    event_dict = {}

    with open(input_file, 'r') as file:
        for line in file:
            event_type, slot, start_date, end_date, event_time = parse_event_line(line)
            for single_date in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
                if single_date not in event_dict:
                    event_dict[single_date] = []
                if event_type in (1, 2):  # If mid or end sem, store with the slot
                    event_dict[single_date].append((event_type, slot, event_time))
                    # Keep only the last three slots
                    event_dict[single_date] = sorted(event_dict[single_date], key=lambda x: x[1])[-3:]
                elif event_type == 0:  # Holiday overrides all slots for that day
                    event_dict[single_date] = [(event_type, None, None)]

    return event_dict

def write_latest_events(event_dict, output_file):
    with open(output_file, 'w') as file:
        for date in sorted(event_dict.keys()):
            events = event_dict[date]
            for event in events:
                event_type, slot, event_time = event
                if event_type == 0:  # Holiday
                    file.write(f"{event_type},{date.strftime('%d-%m-%Y')}\n")
                elif event_type in (1, 2):  # Mid-sem or End-sem
                    file.write(f"{event_type},{slot},{date.strftime('%d-%m-%Y')},{event_time.strftime('%H:%M:%S') if event_time else ''}\n")

# File paths for Raspberry Pi
input_file = os.path.join(os.path.dirname(__file__), "input.txt")
output_file = os.path.join(os.path.dirname(__file__), "latest_events.txt")

# Process the input and update the latest events file
event_dict = read_and_process_events(input_file)
write_latest_events(event_dict, output_file)
