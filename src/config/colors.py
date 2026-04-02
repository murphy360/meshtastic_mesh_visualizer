"""
Color definitions for the mesh visualizer
"""

# Node colors based on last heard status
COLOR_PRIMARY_NODE = 'purple'
COLOR_SEEN_LAST_HOUR = 'green'
COLOR_SEEN_LAST_DAY = 'blue'
COLOR_SEEN_LAST_WEEK = 'orange'
COLOR_SEEN_OVER_WEEK = 'gray'
COLOR_NO_LAST_HEARD = 'red'

# Infrastructure node icon
ICON_INFRASTRUCTURE = 'server'
ICON_AIRCRAFT = 'plane'

# Connection colors
COLOR_CONNECTION_DEFAULT = 'green'
COLOR_CONNECTION_NON_PRIMARY = 'gray'

# Feature colors
COLOR_PRECISION_CIRCLE = 'red'
COLOR_RECEIVE_RANGE = 'lightblue'
COLOR_RECEIVE_RANGE_1HOP = 'lightgreen'
COLOR_RECEIVE_RANGE_2HOP = 'lightyellow'
COLOR_RECEIVE_RANGE_3HOP = 'lightcoral'

# Color mapping for age groups
AGE_GROUP_COLORS = {
    'last_hour': COLOR_SEEN_LAST_HOUR,
    'last_day': COLOR_SEEN_LAST_DAY,
    'last_week': COLOR_SEEN_LAST_WEEK,
    'over_week': COLOR_SEEN_OVER_WEEK,
    'no_last_heard': COLOR_NO_LAST_HEARD
}

# Hop range colors
HOP_RANGE_COLORS = {
    0: COLOR_RECEIVE_RANGE,
    1: COLOR_RECEIVE_RANGE_1HOP,
    2: COLOR_RECEIVE_RANGE_2HOP,
    3: COLOR_RECEIVE_RANGE_3HOP
}

# Opacity settings for polygons
HOP_RANGE_OPACITY = {
    0: 0.3,
    1: 0.25,
    2: 0.2,
    3: 0.15
}
