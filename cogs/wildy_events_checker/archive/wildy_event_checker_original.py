from datetime import datetime, timedelta
import pytz
import re


default_year = datetime.now().year
print(f"\nDefault year: {default_year}")
default_timezone = pytz.timezone('US/Eastern')
print(f"Default timezone: {default_timezone}")

desired_time_converted_to_gmt = None  # Initial value for the desired time

def menu():
    global desired_time_converted_to_gmt #  = None  # Initial value for the desired time
    
    while True:
        print("\nMenu:")
        print("1. Find event")
        print("2. Change year")
        print("3. Change timezone")
        print("4. Exit")

        choice = input("Enter your choice: ")

        if choice == '1':
            if desired_time_converted_to_gmt is None:
                desired_time = get_desired_time()
                desired_time_converted_to_gmt = convert_to_gmt(desired_time)

            current_event = find_current_events(desired_time_converted_to_gmt)
            get_surrounding_events(list_of_events, current_event)
            desired_time_converted_to_gmt = None  # Reset the desired time after finding the event
        elif choice == '2':
            change_year()
        elif choice == '3':
            change_timezone()
        elif choice == '4':
            break


available_timezones = [
    'US/Eastern',
    'US/Central',
    'US/Mountain',
    'US/Pacific',
    'US/Alaska',
    'US/Hawaii',
    'GMT'
]


def get_desired_time():
    """ Function to collect desired date and time from the user """
    
    def get_date_and_time():
        """ Function that combines date and time validation """
        month, day = validate_date()
        hour = validate_time()

        return month, day, hour

    # Call to validate and get date/time input
    month, day, hour = get_date_and_time()

    # Build desired datetime object
    desired_time = datetime(default_year, month, day, hour, 0)
    print(f"Desired Time: {desired_time}")
    return desired_time


def validate_date():
    """ Function to validate user input date """
    pattern = r"^\d{1,2}-\d{1,2}$"
    while True: 
        user_input = input("Enter date 'mm-dd'; month/day are 1 or 2 numbers: ")

        if re.match(pattern, user_input):
            month, day = map(int, user_input.split('-'))
            print(f"Month: {month}, Day: {day}")
            return month, day 
        else: 
            print("Invalid input, please try again")


def validate_time():
    """ Function to validate and convert time to 24-hour format """
    pattern = r"^(\d{1,2})(am|pm)$"
    while True:
        user_input = input("Enter a time ('8am', '11pm'): ").strip().lower()
        match = re.match(pattern, user_input)

        if match:
            hour = int(match.group(1))
            period = match.group(2)

            if 1 <= hour <= 12:
                if period == "pm" and hour != 12:
                    hour += 12
                elif period == "am" and hour == 12:
                    hour = 0
                print(f"Converted time: {hour}:00")
                return hour
            else:
                print("Invalid input: Hour must be between 1 and 12. Please try again.")
        else:
            print("Invalid input format. Please enter a valid time (e.g., '8am', '11pm').")


def convert_to_gmt(desired_time):
    """ Converts the given desired time to GMT based on default timezone """
    if default_timezone.zone != 'GMT':
        desired_local_time = default_timezone.localize(desired_time)
        desired_time_converted_to_gmt = desired_local_time.astimezone(pytz.utc)
        print("Time converted to GMT (UTC):", desired_time_converted_to_gmt)
        return desired_time_converted_to_gmt
    else:
        desired_time_converted_to_gmt = pytz.utc.localize(desired_time)
        print("Time already in GMT (UTC):", desired_time_converted_to_gmt)
        return desired_time_converted_to_gmt
    

def change_timezone():
    global default_timezone
    print("Available timezones:")
    for i, timezone in enumerate(available_timezones):
        if timezone == 'GMT':
            print(f"{i+1}. {timezone} (In-game time)")
        else:
            print(f"{i+1}. {timezone}")
    choice = input("Enter your choice: ")
    if not choice.isdigit() or int(choice) < 1 or int(choice) > len(available_timezones):
        print("Invalid choice")
    else:
        default_timezone = pytz.timezone(available_timezones[int(choice) - 1])
        print(f"Timezone changed to: {default_timezone}")


def change_year():
    global default_year
    year = input("Enter year (YYYY): ")
    if not year.isdigit():
        print("Invalid year")
    elif len(year) != 4:
        print("Year must be 4 digits")
    elif int(year) < 2024:
        print("Year must be 2024 or later")
    else:
        default_year = int(year)
        print(f"Default year changed to: {default_year}")


initial_start_time = datetime(2024, 10, 7, 7, 0, tzinfo=pytz.utc)

events = {
    0: {"name": "Spider Swarm", "is_special": False},                
    1: {"name": "Unnatural Outcrop", "is_special": False},           
    2: {"name": "Stryke the Wyrm", "is_special": True},              # Special event
    3: {"name": "Demon Stragglers", "is_special": False},            
    4: {"name": "Butterfly Swarm", "is_special": False},             
    5: {"name": "King Black Dragon Rampage", "is_special": True},    # Special event
    6: {"name": "Forgotten Soldiers", "is_special": False},          
    7: {"name": "Surprising Seedlings", "is_special": False},        
    8: {"name": "Hellhound Pack", "is_special": False},              
    9: {"name": "Infernal Star", "is_special": True},                # Special event
    10: {"name": "Lost Souls", "is_special": False},                 
    11: {"name": "Ramokee Incursion", "is_special": False},          
    12: {"name": "Displaced Energy", "is_special": False},           
    13: {"name": "Evil Bloodwood Tree", "is_special": True},         # Special event
}

list_of_events = []
for event in events.values():
    if event["is_special"]:
        list_of_events.append(f"{event['name']} (Special)")
    else:
        list_of_events.append(event["name"])


def find_current_events(desired_time_converted_to_gmt):
    # Time elapsed since the initial start
    time_elapsed = desired_time_converted_to_gmt - initial_start_time
    
    hours_since_start = int(time_elapsed.total_seconds() // 3600)
    minutes_past = int((time_elapsed.total_seconds() // 60) % 60)

    #print(f'Time elapsed: {hours_since_start} hours, {minutes_past} minutes')
    
    # Base event index based on hours since the start
    current_event_index = hours_since_start % len(list_of_events)

    # Determine previous, current, and next events
    #previous_event = events[(current_event_index - 1) % len(events)]  # Previous event
    #next_event = events[(current_event_index + 1) % len(events)]  # Next event

    current_event = list_of_events[current_event_index]
    print(f"Current event: {current_event}")
    return current_event


def get_surrounding_events(event_list, current_event):
    list_length = len(event_list)
    current_event_index = event_list.index(current_event)
    n = 3

    def get_before_and_after(event_list, current_event_index, n):

        #before = current_event_index - n % list_length
        #after = current_event_index + n % list_length
        before = []
        after = []

        for i in range(n):
            index_before = (current_event_index - n + i) % list_length
            before.append(event_list[index_before])

            index_after = (current_event_index + i + 1) % list_length
            after.append(event_list[index_after])
        
        return before, after

    before, after = get_before_and_after(event_list, current_event_index, n)

    full_list = before + [current_event] + after
    #print(f"Events surrounding the current event: {full_list}")
    print(f"Events surrounding the current event:")
    
    for item in full_list:
        if item != current_event:
            print(f"    {item}")
        else:
            print(f"--> {item}")
    return




    # current_event_index = list(events.keys())[list(events.values()).index(current_event)]

    # previous_event = events[(current_event_index - 1) % len(events)]  # Previous event
    # next_event = events[(current_event_index + 1) % len(events)]  # Next event

if __name__ == "__main__":
    # This block will only be executed if the script is run directly
    menu()
