import time
import RPi.GPIO as GPIO
from datetime import datetime, timedelta

# Setup GPIO pin
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)

# Function to simulate ringing the bell using GPIO
def ring_bell(duration):
    print(f"Bell ringing for {duration} seconds", flush=True)
    GPIO.output(4, GPIO.HIGH)  # Activate GPIO pin 4 (bell on)
    time.sleep(duration)
    GPIO.output(4, GPIO.LOW)   # Deactivate GPIO pin 4 (bell off)
    print("Bell stopped", flush=True)

# Function to process the latest events file
def process_latest_events(input_file):
    date_events = {}
    immediate_ring = False  # Flag for immediate bell ring
    specific_time_event = None  # To track specific time events

    with open(input_file, 'r') as infile:
        for line in infile:
            line = line.strip()
            if line:
                parts = line.split(',')
                event_type = int(parts[0])

                if event_type == 0:
                    # Holiday event
                    date_str = parts[1]
                    date_events[date_str] = {'event': (event_type, None, None)}
                elif event_type == 1 or event_type == 2:
                    # MID SEM or END SEM
                    slot = int(parts[1])
                    date_str = parts[2]
                    event_time = parts[3] if len(parts) > 3 else None
                    if date_str not in date_events:
                        date_events[date_str] = {}
                    date_events[date_str][slot] = event_time
                elif event_type == 3:
                    # Specific time bell event
                    specific_time_event = parts[1]  # Capture the specific time
                    immediate_ring = True

    return date_events, immediate_ring, specific_time_event

# MID SEM and END SEM slot offsets
midsem_offsets = {
    1: [timedelta(minutes=11), timedelta(minutes=30), timedelta(minutes=43), timedelta(hours=2, minutes=15), timedelta(hours=2, minutes=30)],
    2: [timedelta(minutes=13, seconds=45), timedelta(minutes=35), timedelta(minutes=48), timedelta(hours=2, minutes=20), timedelta(hours=2, minutes=35)],
    3: [timedelta(minutes=13), timedelta(minutes=40), timedelta(minutes=53), timedelta(hours=2, minutes=25), timedelta(hours=2, minutes=40)]
}

endsem_offsets = {
    1: [timedelta(minutes=15), timedelta(minutes=32), timedelta(minutes=30), timedelta(hours=3), timedelta(hours=3, minutes=30)],
    2: [timedelta(minutes=20), timedelta(minutes=37), timedelta(minutes=35), timedelta(hours=3, minutes=5), timedelta(hours=3, minutes=35)],
    3: [timedelta(minutes=46), timedelta(minutes=42), timedelta(minutes=40), timedelta(hours=3, minutes=10), timedelta(hours=3, minutes=40)]
}

# Normal weekday and Saturday bell times
normal_weekday_times = ["09:00:00", "10:00:00", "11:00:00", "12:00:00", "13:00:00", "14:00:00", "15:00:00", "16:00:00"]
normal_weekday_warning_times = ["08:55:00", "09:55:00", "10:55:00", "11:55:00", "12:55:00", "13:55:00", "14:55:00", "15:55:00"]

normal_saturday_times = ["09:00:00", "10:00:00", "11:00:00", "12:00:00", "13:00:00"]
normal_saturday_warning_times = ["08:55:00", "09:55:00", "10:55:00", "11:55:00", "12:55:00"]

# Function to calculate bell times for MID SEM or END SEM
def calculate_bell_times(base_time_str, offsets):
    base_time = datetime.strptime(base_time_str, "%H:%M:%S")
    return [(base_time + offset).strftime("%H:%M:%S") for offset in offsets]

# Paths to the input text file
input_file_path = "C:\\BELL\\latest_events.txt"  # Path to the latest events text file

def main_loop():
    print("Starting the main loop...")

    printed_slots = {}  # Track printed slots for each date and each slot separately
    midsem_times = {}  # Store calculated MID SEM times for display
    displayed_midsem_times = set()  # Track displayed MID SEM times to avoid duplication

    while True:
        now = datetime.now()
        current_time_str = now.strftime("%H:%M:%S")
        current_date = now.strftime("%d-%m-%Y")
        current_weekday = now.strftime("%A")

        # Print the current date and time
        print(f"Checking updates at {current_time_str} on {current_date} ({current_weekday})")

        # Process the latest events file
        date_events, immediate_ring, specific_time_event = process_latest_events(input_file_path)

        # Check for specific time bell event (type 3)
        if specific_time_event and current_time_str == specific_time_event:
            print(f"Specific time bell ring triggered at {current_time_str}")
            ring_bell(5)  # Ring the bell at the specific time for 5 seconds

        # Check if there are any events for the current date
        if current_date in date_events:
            event_info = date_events[current_date]
            if isinstance(event_info, dict):  # Handle MID SEM or END SEM
                if current_date not in printed_slots:
                    printed_slots[current_date] = set()
                for slot, time_str in event_info.items():
                    if time_str:  # Only process if there's a valid time
                        result_times = calculate_bell_times(time_str, midsem_offsets.get(slot, []))
                        print(f"Date: {current_date}, MID SEM Slot: {slot}, Times: {result_times}")
                        midsem_times[current_date] = midsem_times.get(current_date, [])
                        midsem_times[current_date].append((slot, result_times))
                        # Bell ringing logic for MID SEM or END SEM
                        if current_time_str in result_times and (current_date, slot) not in printed_slots[current_date]:
                            ring_bell(8)  # Ring the bell for 8 seconds
                            printed_slots[current_date].add((current_date, slot))  # Track that this slot has been processed
            elif 'event' in event_info:  # Handle Holiday
                event_type, slot, event_time = event_info['event']
                if event_type == 0:
                    print(f"Date: {current_date}, Event: Holiday Type 0")
                # Bell ringing logic for holidays, if needed
        else:
            # Handle normal timings if no events for today
            if current_weekday == "Sunday":
                print(f"{current_date} is a Sunday. No specific actions required.")
            elif current_weekday == "Saturday":
                if current_time_str in normal_saturday_warning_times:
                    print(f"Regular Saturday warning bell ring at {current_time_str} for 8 seconds.")
                    ring_bell(8)
                elif current_time_str in normal_saturday_times:
                    print(f"Regular Saturday bell ring at {current_time_str} for 5 seconds.")
                    ring_bell(5)
            else:
                if current_time_str in normal_weekday_warning_times:
                    print(f"Regular weekday warning bell ring at {current_time_str} for 8 seconds.")
                    ring_bell(8)
                elif current_time_str in normal_weekday_times:
                    print(f"Regular weekday bell ring at {current_time_str} for 5 seconds.")
                    ring_bell(5)

        time.sleep(1)  # Wait for 1 second before checking again

# Clean up GPIO on program exit
try:
    main_loop()
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()  # Ensure the GPIO is cleaned up properly when the program exits
