import asyncio
from anthropic.types import ToolParam
from datetime import datetime, timedelta 
from desktop_notifier import DesktopNotifier, DEFAULT_SOUND


def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    
    return datetime.now().strftime(date_format)


def add_duration_to_datetime(datetime_str, date_format="%Y-%m-%d %H:%M:%S", duration=0, unit="days"):
    date = datetime.strptime(datetime_str, date_format)

    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [
                31,
                29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                31,
                30,
                31,
                30,
                31,
                31,
                30,
                31,
                30,
                31,
            ][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


async def schedule_notification(title:str, content:str, delay_seconds=0):

    delay_seconds = int(delay_seconds)
    
    notifier = DesktopNotifier()

    await asyncio.sleep(delay_seconds)
    
    await notifier.send(
            title=title,
            message=content,
            timeout=0.5,
            sound=DEFAULT_SOUND,
        )

    return "Notification was successfully sent"