"""
Time-related utility functions
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


def time_since_last_heard(last_heard_time: datetime) -> str:
    """Convert a datetime to a human-readable time since string"""
    now = datetime.now(timezone.utc)
    delta = now - last_heard_time
    seconds = delta.total_seconds()
    
    if seconds < 60:  # Less than a minute, return seconds
        return f"{int(seconds)}s"
    elif seconds < 3600:  # Less than an hour, return minutes
        return f"{int(seconds // 60)}m"
    elif seconds < 86400:  # Less than a day, return hours
        return f"{int(seconds // 3600)}h"
    elif seconds < 604800:  # Less than a week, return days
        return f"{int(seconds // 86400)}d"
    elif seconds < 2592000:  # Less than a month, return weeks
        return f"{int(seconds // 604800)}w"
    elif seconds < 31536000:  # Less than a year, return months
        return f"{int(seconds // 2592000)}m"
    else:  # More than a year, return years
        return f"{int(seconds // 31536000)}y"


def get_age_group(last_heard_time: Optional[datetime]) -> str:
    """Determine the age group based on last heard time"""
    if not last_heard_time:
        return 'no_last_heard'
    
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)
    
    if last_heard_time > one_hour_ago:
        return 'last_hour'
    elif last_heard_time > one_day_ago:
        return 'last_day'
    elif last_heard_time > one_week_ago:
        return 'last_week'
    else:
        return 'over_week'


def get_time_thresholds():
    """Get datetime objects for age group thresholds"""
    now = datetime.now(timezone.utc)
    return {
        'now': now,
        'one_hour_ago': now - timedelta(hours=1),
        'one_day_ago': now - timedelta(days=1),
        'one_week_ago': now - timedelta(weeks=1)
    }
