"""
Application settings and configuration
"""
import os
from datetime import datetime

# File paths - use test data for development on Windows
if os.name == 'nt':  # Windows
    # Use test data directory relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    default_mesh_file = os.path.join(project_root, 'tests', 'data', 'mesh_data_small.json')
else:  # Linux/Docker
    default_mesh_file = '/data/mesh_data.json'

MESH_DATA_FILE = os.getenv('MESH_DATA_FILE', default_mesh_file)

# Application settings
REFRESH_INTERVAL_SECONDS = 10
MAP_ZOOM_START = 12
PRIMARY_NODE_ALTITUDE_OFFSET = 100  # meters to add to primary node altitude

# Default visibility settings
DEFAULT_VISIBILITY_SETTINGS = {
    'show_last_hour': True,
    'show_last_day': True,
    'show_last_week': False,
    'show_over_week': False,
    'show_no_last_heard': False,
    'show_receive_range': False,
    'show_receive_range_1hop': False,
    'show_receive_range_2hop': False,
    'show_receive_range_3hop': False,
    'show_range_rings': True
}

# Time thresholds
AIRCRAFT_ALTITUDE_THRESHOLD = 5000  # meters

# Map styling
MAP_KEY_POSITION = {
    'bottom': '50px',
    'right': '10px',
    'width': '360px',
    'height': '380px'
}

SITREP_POSITION = {
    'top': '120px',
    'right': '10px',
    'width': '300px'
}

NODE_LIST_SIDEBAR = {
    'width': '300px'
}

# Age-based marker sizing (radius in pixels for CircleMarker)
MARKER_SIZE_BY_AGE = {
    'last_hour': 10,
    'last_day': 7,
    'last_week': 4,
    'over_week': 2,
    'no_last_heard': 2
}

# Precision radius calculations (in meters)
PRECISION_RADIUS_MAP = {
    0: 0,
    11: 11672.736900000944,  # 11 bits ~ 11km
    12: 5836.362884000802,   # 12 bits ~ 5.8km
    13: 2918.1758760007315,  # 13 bits ~ 2.9km
    14: 1459.0823719999053,  # 14 bits ~ 1.5km
    15: 729.5356200010741,   # 15 bits ~ 730m
    16: 364.7622440000765,   # 16 bits ~ 365m
    32: 0                    # Full precision
}
