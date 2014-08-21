from datetime import datetime

def timestamp_to_string():
    """ Converts the current datetime to a string."""
    return "["+datetime.now().strftime("%I:%M:%S %p")+"]"