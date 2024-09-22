import pytz
from datetime import datetime
from datetime import datetime, time
from zoneinfo import ZoneInfo

def get_copenhagen_time():
    copenhagen_tz = pytz.timezone('Europe/Copenhagen')
    current_time = datetime.now(copenhagen_tz)
    formatted_time = current_time.strftime("%-I:%M%p")
    return formatted_time.lower()

def get_copenhagen_datetime():
    copenhagen_tz = pytz.timezone('Europe/Copenhagen')
    current_time = datetime.now(copenhagen_tz)
    return current_time.strftime("%A, %B %d, %Y %I:%M %p")

print(get_copenhagen_datetime())

def get_copenhagen_time_between_3am_and_4am():
    copenhagen_tz = pytz.timezone('Europe/Copenhagen')
    current_time = datetime.now(copenhagen_tz)
    current_time = current_time.time()
    if time(3, 0) <= current_time < time(4, 0):
        return True
    return False

def is_notification_appropriate_time(current_time=None):
    # If no time is provided, use the current time in Copenhagen
    if current_time is None:
        current_time = datetime.now(ZoneInfo("Europe/Copenhagen"))
    
    # Extract day of week (0 is Monday, 6 is Sunday) and time
    day_of_week = current_time.weekday()
    current_time = current_time.time()
    
    # Check if it's a weekday (Monday to Friday)
    if day_of_week < 5:
        # Weekday rules
        if time(22, 0) <= current_time or current_time < time(7, 0):
            return False  # Don't notify between 10 PM and 7 AM
        if time(9, 0) <= current_time < time(16, 30):
            return False  # Don't notify between 9 AM and 4:30 PM
    else:
        # Weekend rules
        if time(23, 0) <= current_time or current_time < time(7, 0):
            return False  # Don't notify between 11 PM and 9 AM
    
    # If we haven't returned False by now, it's okay to notify
    return True