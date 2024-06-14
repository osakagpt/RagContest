from datetime import timedelta


def format_millisec(milliseconds: int) -> str:
    # Convert milliseconds to seconds and microseconds
    seconds, millis = divmod(milliseconds, 1000)
    # Create a timedelta object
    delta = timedelta(seconds=seconds, milliseconds=millis)
    # Extract hours, minutes, and seconds from the timedelta object
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    # Format the time string
    time_string = f"{hours:02}:{minutes:02}:{seconds:02}.{delta.microseconds // 1000:03}"
    return time_string
