import json
import logging
import os
import time
import threading
import folium
from datetime import datetime, timezone, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from flask import Flask, render_template, make_response, request, jsonify

# Configure logging
logging.basicConfig(format='%(asctime)s - %(filename)s:%(lineno)d - %(message)s', level=logging.INFO)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching of static files

MESH_DATA_FILE = os.getenv('MESH_DATA_FILE', '/data/mesh_data.json')

# Define color variables
COLOR_PRIMARY_NODE = 'purple'
COLOR_SEEN_LAST_HOUR = 'green'
COLOR_SEEN_LAST_DAY = 'blue'
COLOR_SEEN_LAST_WEEK = 'orange'
COLOR_SEEN_OVER_WEEK = 'gray'
COLOR_NO_LAST_HEARD = 'red'
COLOR_CONNECTION_DEFAULT = 'green'
COLOR_CONNECTION_NON_PRIMARY = 'gray'
COLOR_PRECISION_CIRCLE = 'red'
COLOR_RECEIVE_RANGE = 'lightblue'

# Sample .json data for mesh nodes
DEFAULT_MESH_DATA = {
    "last_update": "2024-04-23T00:00:00Z",
    "sitrep_time": "2024-04-23T00:00:00Z",
    "nodes": [
        {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "lastHeard": "", "hopsAway": 0, "connections": ["node2", "node3"]},
        {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "lastHeard": "1739400886", "hopsAway": 0, "connections": ["node1"]},
        {"id": "node3", "lat": 0, "lon": 0, "alt": 0, "lastHeard": "1739400960", "hopsAway": 1, "connections": ["node1"]},
        {"id": "node4", "lat": 37.7849, "lon": -122.4094, "alt": 15, "lastHeard": "1739400800", "hopsAway": 0, "connections": ["node1"]},
        {"id": "node5", "lat": 37.7649, "lon": -122.4294, "alt": 25, "lastHeard": "1739400900", "hopsAway": 0, "connections": ["node1"]}
    ],
    "sitrep": [
        "CQ CQ CQ de DPMM.  My 1801Z 15 Feb 2025 SITREP is as follows:", 
        "Line 1: Direct Nodes online: 5 ( DP00 DPBP DPST DPBS DPTT)", 
        "Line 2: Aircraft Tracks: ", "Line 3: Nodes of Interest: ", 
        "Line 4: Packets Received: 1", 
        "Line 5: Uptime: 15 Days, 21 Hours, 45 Minutes, 33 Seconds. Reconnections: 1", 
        "Line 6: Intentions: Continue to track and report. Send 'Ping' to test connectivity. Send 'Sitrep' to request a report", 
        "de DPMM out"
    ]
}

mesh_data = DEFAULT_MESH_DATA

@app.route('/')
def index():
    logging.info("Request received for index.")
    return update_map()

@app.route('/refresh')
def refresh_data():
    """Manual refresh endpoint"""
    logging.info("Manual refresh requested")
    read_mesh_data()
    return jsonify({"status": "refreshed", "timestamp": datetime.now().isoformat()})

@app.route('/get_mesh_data')
def get_mesh_data_endpoint():
    """Return current mesh data as JSON for live updates"""
    read_mesh_data()
    return jsonify({
        "last_update": mesh_data.get("last_update", "N/A"),
        "nodes": mesh_data.get("nodes", []),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/filter_map')
def filter_map():
    """Create a filtered map based on visibility toggles"""
    # Get visibility parameters for each age group
    show_last_hour = request.args.get('show_last_hour', 'true').lower() == 'true'
    show_last_day = request.args.get('show_last_day', 'true').lower() == 'true'
    show_last_week = request.args.get('show_last_week', 'true').lower() == 'true'
    show_over_week = request.args.get('show_over_week', 'true').lower() == 'true'
    show_no_last_heard = request.args.get('show_no_last_heard', 'true').lower() == 'true'
    show_receive_range = request.args.get('show_receive_range', 'false').lower() == 'true'
    
    visibility_settings = {
        'show_last_hour': show_last_hour,
        'show_last_day': show_last_day,
        'show_last_week': show_last_week,
        'show_over_week': show_over_week,
        'show_no_last_heard': show_no_last_heard,
        'show_receive_range': show_receive_range
    }
    
    logging.info(f"Filtering map with visibility settings: {visibility_settings}")
    
    read_mesh_data()
    m = create_map(visibility_settings=visibility_settings)
    
    unique_map_filename = f"map_filtered_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    m.save(f"templates/{unique_map_filename}")
    
    response = render_template(unique_map_filename)
    return response

def read_mesh_data():
    global mesh_data
    try:
        logging.info(f"Reading mesh data from file: {MESH_DATA_FILE}")
        with open(MESH_DATA_FILE, 'r') as f:
            new_mesh_data = json.load(f)
        
        # Check if data has changed
        if mesh_data != new_mesh_data:
            logging.info("Mesh data has changed, updating...")
            mesh_data = new_mesh_data
        else:
            logging.debug("Mesh data unchanged")
        
        # Always update the last_update timestamp to show when we last checked
        mesh_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
        logging.debug(f"Current mesh data timestamp: {mesh_data.get('last_update', 'N/A')}")
    except FileNotFoundError:
        logging.warning(f"Mesh data file not found at {MESH_DATA_FILE}. Using default data.")
        mesh_data = DEFAULT_MESH_DATA
        mesh_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing mesh data JSON: {e}. Using default data.")
        mesh_data = DEFAULT_MESH_DATA
        mesh_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    except Exception as e:
        logging.error(f"Unexpected error reading mesh data: {e}. Using default data.")
        mesh_data = DEFAULT_MESH_DATA
        mesh_data['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

def time_since_last_heard(last_heard_time):
    now = datetime.now(timezone.utc)
    delta = now - last_heard_time
    seconds = delta.total_seconds()
    if seconds < 60: # Less than a minute, return seconds
        return f"{int(seconds)}s"
    elif seconds < 3600: # Less than an hour, return minutes
        return f"{int(seconds // 60)}m"
    elif seconds < 86400: # Less than a day, return hours
        return f"{int(seconds // 3600)}h"
    elif seconds < 604800: # Less than a week, return days
        return f"{int(seconds // 86400)}d"
    elif seconds < 2592000: # Less than a month, return weeks
        return f"{int(seconds // 604800)}w"
    elif seconds < 31536000: # Less than a year, return months
        return f"{int(seconds // 2592000)}m"
    else: # More than a year, return years
        return f"{int(seconds // 31536000)}y"

def calculate_precision_radius(precision_bits):
    """
    Calculate radius in meters based on precision_bits
    Lower precision_bits means less precision (larger radius)
    """
    if precision_bits is None:
        return None
    
    # Simplified calculation: higher precision_bits = smaller radius
    # This is a rough approximation, adjust as needed
    if precision_bits == 0:
        return 0
    elif precision_bits <= 11:
        return 11672.736900000944 # 11 bits ~ 11km
    elif precision_bits == 12:
        return 5836.362884000802 # 12 bits ~ 5.8km
    elif precision_bits == 13:
        return 2918.1758760007315 # 13 bits ~ 2.9km
    elif precision_bits == 14:
        return 1459.0823719999053 # 14 bits ~ 1.5km
    elif precision_bits == 15:
        return 729.5356200010741 # 15 bits ~ 730m
    elif precision_bits == 16:
        return 364.7622440000765 # 16 bits ~ 365m
    elif precision_bits == 32: # Full precision
        return 0    # No radius for full precision
    else:
        return 0    

def is_aircraft(node):
    """
    Determine if a node represents an aircraft based on altitude > 5000m
    """
    altitude = node.get('alt', 0)
    return altitude > 5000

def create_receive_range_polygon(nodes, main_node, visibility_settings):
    """
    Create a polygon around all nodes with 0 hops to show primary node receive range
    Only includes nodes that are currently visible based on visibility settings
    """
    import math
    from datetime import datetime, timezone, timedelta
    
    # Time thresholds for age groups
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)
    
    # Get all nodes with 0 hops that have valid positions and are currently visible
    zero_hop_nodes = []
    for node in nodes:
        if (node.get('hopsAway', -1) == 0 and 
            node['lat'] != 0 and node['lon'] != 0 and 
            node != main_node):  # Exclude the main node itself
            
            # Check if this node would be visible based on age and visibility settings
            node_should_show = True
            
            if 'lastHeard' in node and node['lastHeard']:
                last_heard_time = datetime.fromtimestamp(int(node['lastHeard']), tz=timezone.utc)
                if last_heard_time > one_hour_ago:
                    node_should_show = visibility_settings.get('show_last_hour', True)
                elif last_heard_time > one_day_ago:
                    node_should_show = visibility_settings.get('show_last_day', True)
                elif last_heard_time > one_week_ago:
                    node_should_show = visibility_settings.get('show_last_week', True)
                else:
                    node_should_show = visibility_settings.get('show_over_week', True)
            else:
                node_should_show = visibility_settings.get('show_no_last_heard', True)
            
            # Only include if the node would be visible
            if node_should_show:
                zero_hop_nodes.append([node['lat'], node['lon']])
    
    # Include the main node in the polygon (always visible)
    if main_node['lat'] != 0 and main_node['lon'] != 0:
        zero_hop_nodes.append([main_node['lat'], main_node['lon']])
    
    if len(zero_hop_nodes) < 3:
        # Need at least 3 points to create a polygon
        return None
        
    try:
        # Simple convex hull algorithm (Gift wrapping / Jarvis march)
        def cross_product(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
        
        def convex_hull(points):
            points = sorted(set(tuple(p) for p in points))
            if len(points) <= 1:
                return points
            
            # Build lower hull
            lower = []
            for p in points:
                while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
                    lower.pop()
                lower.append(p)
            
            # Build upper hull
            upper = []
            for p in reversed(points):
                while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
                    upper.pop()
                upper.append(p)
            
            return lower[:-1] + upper[:-1]
        
        hull_points = convex_hull(zero_hop_nodes)
        
        # Convert back to list of [lat, lon] pairs
        polygon_coords = [[float(p[0]), float(p[1])] for p in hull_points]
        
        return polygon_coords
    except Exception as e:
        logging.warning(f"Could not create receive range polygon: {e}")
        return None

def create_map(visibility_settings=None):
    # Default visibility settings (all visible)
    if visibility_settings is None:
        visibility_settings = {
            'show_last_hour': True,
            'show_last_day': True,
            'show_last_week': False,
            'show_over_week': False,
            'show_no_last_heard': False,
            'show_receive_range': False
        }
    
    main_node = mesh_data["nodes"][0]
    logging.info(f"Main node: {main_node}")
    main_node['alt'] += 100  # Add 100 meters to the primary node's altitude

    logging.info(f"Creating map centered around {main_node['id']} at {main_node['lat']}, {main_node['lon']} with visibility: {visibility_settings}.")
    m = folium.Map(location=[main_node['lat'], main_node['lon']], zoom_start=12)

    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)

    nodes_without_position = []
    filtered_nodes_count = 0
    total_nodes_count = 0
    age_group_counts = {
        'last_hour': 0,
        'last_day': 0,
        'last_week': 0,
        'over_week': 0,
        'no_last_heard': 0
    }

    for node in mesh_data["nodes"][1:]:
        total_nodes_count += 1

        node_is_aircraft = is_aircraft(node)
        
        if 'lastHeard' in node:
            last_heard_time = datetime.fromtimestamp(int(node['lastHeard']), tz=timezone.utc)
            last_heard = time_since_last_heard(last_heard_time)
        else:
            last_heard = "N/A"
            last_heard_time = None
            
        # Determine age group and color
        if last_heard_time:
            if last_heard_time > one_hour_ago:
                color = COLOR_SEEN_LAST_HOUR
                age_group = 'last_hour'
                should_show = visibility_settings.get('show_last_hour', True)
            elif last_heard_time > one_day_ago:
                color = COLOR_SEEN_LAST_DAY
                age_group = 'last_day'
                should_show = visibility_settings.get('show_last_day', True)
            elif last_heard_time > one_week_ago:
                color = COLOR_SEEN_LAST_WEEK
                age_group = 'last_week'
                should_show = visibility_settings.get('show_last_week', True)
            else:
                color = COLOR_SEEN_OVER_WEEK
                age_group = 'over_week'
                should_show = visibility_settings.get('show_over_week', True)
        else:
            color = COLOR_NO_LAST_HEARD
            age_group = 'no_last_heard'
            should_show = visibility_settings.get('show_no_last_heard', True)

        age_group_counts[age_group] += 1
        
        # Apply visibility filter - skip nodes that are hidden
        if not should_show:
            filtered_nodes_count += 1
            continue

        node['color'] = color
        node['last_heard_str'] = last_heard
        node['last_heard_time'] = last_heard_time
        node['age_group'] = age_group
        node['is_aircraft'] = node_is_aircraft

        if node['lat'] == 0 or node['lon'] == 0:
            nodes_without_position.append(node)
        else:
            # Use plane icon for aircraft, regular marker for others
            if node_is_aircraft:
                icon = folium.Icon(color=color, icon='plane', prefix='fa')
                popup_text = f"✈️ {node['id']} (Aircraft)<br>Altitude: {node['alt']}m<br>Last Heard: {last_heard}"
            else:
                icon = folium.Icon(color=color)
                popup_text = f"{node['id']}<br>Altitude: {node['alt']}m<br>Last Heard: {last_heard}"
            
            if node.get('hopsAway', 0) != 0:
                popup_text += f"<br>Hops Away: {node['hopsAway']}"
            
            # Add precision info to popup if available
            if 'precision_bits' in node:
                logging.info(f"Node {node['id']} has precision bits: {node['precision_bits']}")
                popup_text += f"<br>Precision: {node['precision_bits']} bits"
            
            marker = folium.Marker(
                location=[node['lat'], node['lon']],
                popup=popup_text,
                icon=icon
            )
            marker.add_to(m)
            
            # Add circle to represent position precision if available
            if 'precision_bits' in node:
                popup_text = f"{node['id']}<br>Altitude: {node['alt']}m<br>Last Heard: {last_heard} \n Precision: {node['precision_bits']} bits"
                radius = calculate_precision_radius(node['precision_bits'])
                if radius and last_heard_time and last_heard_time > one_day_ago:
                    if radius > 0:  
                        folium.Circle(
                            location=[node['lat'], node['lon']],
                            radius=radius,
                            color=COLOR_PRECISION_CIRCLE,
                            fill=True,
                            fill_opacity=0.1,
                            popup=popup_text
                        ).add_to(m)

    # Always add the main node (primary node)
    icon = folium.Icon(color=COLOR_PRIMARY_NODE, icon='star', prefix='fa')
    main_marker = folium.Marker(
        location=[main_node['lat'], main_node['lon']],
        popup=f"{main_node['id']}<br>Altitude: {main_node['alt']}m",
        icon=icon
    )
    main_marker.add_to(m)
    
    # Add precision circle for main node if available
    if 'precision_bits' in main_node:
        popup_text = f"{main_node['id']}<br>Altitude: {main_node['alt']}m<br>Precision: {main_node['precision_bits']} bits"
        radius = calculate_precision_radius(main_node['precision_bits'])
        if radius:
            if radius > 0:
                folium.Circle(
                    location=[main_node['lat'], main_node['lon']],
                    radius=radius,
                    color=COLOR_PRECISION_CIRCLE,
                    fill=True,
                    fill_opacity=0.1,
                    popup=popup_text
                ).add_to(m)

    # Add connections (only for nodes that are visible)
    for node in mesh_data["nodes"]:
        if node['lat'] == 0 or node['lon'] == 0:
            continue
            
        # Check if this node is visible
        if node != main_node:  # Skip visibility check for main node
            if 'lastHeard' in node:
                last_heard_time = datetime.fromtimestamp(int(node['lastHeard']), tz=timezone.utc)
                if last_heard_time > one_hour_ago:
                    should_show = visibility_settings.get('show_last_hour', True)
                elif last_heard_time > one_day_ago:
                    should_show = visibility_settings.get('show_last_day', True)
                elif last_heard_time > one_week_ago:
                    should_show = visibility_settings.get('show_last_week', True)
                else:
                    should_show = visibility_settings.get('show_over_week', True)
            else:
                should_show = visibility_settings.get('show_no_last_heard', True)
            
            if not should_show:
                continue  # Skip connections for hidden nodes
        
        for connection in node['connections']:
            connected_node = next((n for n in mesh_data["nodes"] if n['id'] == connection), None)
            if connected_node and connected_node['lat'] != 0 and connected_node['lon'] != 0:
                # Check if connected node is also visible
                if connected_node != main_node:  # Skip visibility check for main node
                    if connected_node['lastHeard']:
                        connected_last_heard = datetime.fromtimestamp(int(connected_node['lastHeard']), tz=timezone.utc)
                        if connected_last_heard > one_hour_ago:
                            connected_should_show = visibility_settings.get('show_last_hour', True)
                        elif connected_last_heard > one_day_ago:
                            connected_should_show = visibility_settings.get('show_last_day', True)
                        elif connected_last_heard > one_week_ago:
                            connected_should_show = visibility_settings.get('show_last_week', True)
                        else:
                            connected_should_show = visibility_settings.get('show_over_week', True)
                    else:
                        connected_should_show = visibility_settings.get('show_no_last_heard', True)
                    
                    if not connected_should_show:
                        continue  # Skip connection if target node is hidden
                
                connection_color = COLOR_CONNECTION_DEFAULT if connection == main_node['id'] else COLOR_CONNECTION_NON_PRIMARY
                folium.PolyLine(
                    locations=[[node['lat'], node['lon']], [connected_node['lat'], connected_node['lon']]],
                    color=connection_color
                ).add_to(m)

    # Add receive range polygon if enabled
    if visibility_settings.get('show_receive_range', False):
        polygon_coords = create_receive_range_polygon(mesh_data["nodes"], main_node, visibility_settings)
        if polygon_coords:
            folium.Polygon(
                locations=polygon_coords,
                color=COLOR_RECEIVE_RANGE,
                weight=3,
                fill=True,
                fillColor=COLOR_RECEIVE_RANGE,
                fillOpacity=0.2,
                popup="Primary Node Receive Range (0-hop nodes)"
            ).add_to(m)
            logging.info(f"Added receive range polygon with {len(polygon_coords)} points")
        else:
            logging.info("Not enough visible 0-hop nodes to create receive range polygon")

    add_interactive_map_key(m, main_node['id'], visibility_settings, age_group_counts)
    add_sitrep_data(m)
    add_nodes_without_position(m, nodes_without_position)

    logging.info(f"Map created with {total_nodes_count - filtered_nodes_count} visible nodes, {filtered_nodes_count} filtered out")
    return m

def add_interactive_map_key(m, primary_node_id, visibility_settings, age_group_counts):
    """Add an interactive map key with clickable visibility toggles"""
    
    # Create visibility indicators
    def get_visibility_indicator(is_visible):
        return "👁️" if is_visible else "❌"
    
    def get_opacity_style(is_visible):
        return "opacity: 1.0;" if is_visible else "opacity: 0.5; text-decoration: line-through;"
    
    key_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 320px; height: 320px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <b>Key - Click to Toggle Visibility</b><br>
        <div style="margin-top: 5px;">
            <div style="margin: 2px 0;">
                <span style="font-size: 12px;">👁️</span>
                <i class="fa fa-star" style="color:{COLOR_PRIMARY_NODE}"></i>&nbsp;{primary_node_id} (Always visible)
            </div>
            <div id="toggle-last-hour" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_last_hour'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_last_hour'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_HOUR}"></i>&nbsp;Last Hour ({age_group_counts['last_hour']})
            </div>
            <div id="toggle-last-day" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_last_day'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_last_day'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_DAY}"></i>&nbsp;Last Day ({age_group_counts['last_day']})
            </div>
            <div id="toggle-last-week" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_last_week'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_last_week'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_WEEK}"></i>&nbsp;Last Week ({age_group_counts['last_week']})
            </div>
            <div id="toggle-over-week" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_over_week'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_over_week'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_OVER_WEEK}"></i>&nbsp;Over Week Ago ({age_group_counts['over_week']})
            </div>
            <div id="toggle-no-last-heard" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_no_last_heard'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_no_last_heard'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_NO_LAST_HEARD}"></i>&nbsp;No Last Heard ({age_group_counts['no_last_heard']})
            </div>
        </div>
        <div style="margin-top: 8px; border-top: 1px solid #ccc; padding-top: 5px;">
            <div id="toggle-receive-range" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings.get('show_receive_range', False))}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings.get('show_receive_range', False))}</span>
                <i class="fa fa-circle-o" style="color:{COLOR_RECEIVE_RANGE}"></i>&nbsp;Receive Range (0-hop polygon)
            </div>
            <div style="margin: 2px 0; font-size: 12px;">
                <i class="fa fa-circle-o" style="color:{COLOR_PRECISION_CIRCLE}"></i>&nbsp;Range Rings - Position Precision
            </div>
            <div style="font-size: 10px; color: gray; margin-left: 15px;">
                Red circles show GPS precision uncertainty<br>
                Shown only for nodes heard within last day
            </div>
        </div>
        <div style="margin-top: 8px; font-size: 11px; color: gray;">
            Visible: {sum(count for key, count in age_group_counts.items() 
                      if visibility_settings.get(f'show_{key}', True))} / {sum(age_group_counts.values())} nodes
        </div>
        <div style="margin-top: 5px; font-size: 10px; color: gray; border-top: 1px solid #eee; padding-top: 3px;" id="last-updated-timestamp">
            Last Updated: {mesh_data.get('last_update', 'N/A')}
        </div>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        function toggleVisibility(group, currentState) {{
            console.log('Toggling visibility for group:', group, 'current state:', currentState);
            
            // Build URL with toggled state
            const url = new URL('/filter_map', window.location.origin);
            const newState = !currentState;
            
            // Set all current visibility states
            url.searchParams.set('show_last_hour', '{str(visibility_settings["show_last_hour"]).lower()}');
            url.searchParams.set('show_last_day', '{str(visibility_settings["show_last_day"]).lower()}');
            url.searchParams.set('show_last_week', '{str(visibility_settings["show_last_week"]).lower()}');
            url.searchParams.set('show_over_week', '{str(visibility_settings["show_over_week"]).lower()}');
            url.searchParams.set('show_no_last_heard', '{str(visibility_settings["show_no_last_heard"]).lower()}');
            url.searchParams.set('show_receive_range', '{str(visibility_settings.get("show_receive_range", False)).lower()}');
            
            // Toggle the specific group
            url.searchParams.set('show_' + group, newState.toString());
            
            console.log('Navigating to:', url.toString());
            window.location.href = url.toString();
        }}
        
        // Add click listeners
        document.getElementById('toggle-last-hour').addEventListener('click', function() {{
            toggleVisibility('last_hour', {str(visibility_settings['show_last_hour']).lower()});
        }});
        
        document.getElementById('toggle-last-day').addEventListener('click', function() {{
            toggleVisibility('last_day', {str(visibility_settings['show_last_day']).lower()});
        }});
        
        document.getElementById('toggle-last-week').addEventListener('click', function() {{
            toggleVisibility('last_week', {str(visibility_settings['show_last_week']).lower()});
        }});
        
        document.getElementById('toggle-over-week').addEventListener('click', function() {{
            toggleVisibility('over_week', {str(visibility_settings['show_over_week']).lower()});
        }});
        
        document.getElementById('toggle-no-last-heard').addEventListener('click', function() {{
            toggleVisibility('no_last_heard', {str(visibility_settings['show_no_last_heard']).lower()});
        }});
        
        document.getElementById('toggle-receive-range').addEventListener('click', function() {{
            toggleVisibility('receive_range', {str(visibility_settings.get('show_receive_range', False)).lower()});
        }});
        
        // Smooth refresh function that only updates timestamps and data
        function refreshData() {{
            fetch('/get_mesh_data')
                .then(response => response.json())
                .then(data => {{
                    // Update the last updated timestamp in the key
                    const lastUpdatedElement = document.getElementById('last-updated-timestamp');
                    if (lastUpdatedElement) {{
                        lastUpdatedElement.textContent = 'Last Updated: ' + data.last_update;
                    }}
                    
                    console.log('Data refreshed at:', data.timestamp);
                }})
                .catch(error => {{
                    console.error('Error refreshing data:', error);
                    // Fall back to full page refresh if data fetch fails after 3 failures
                    if (!window.refreshFailures) window.refreshFailures = 0;
                    window.refreshFailures++;
                    if (window.refreshFailures >= 3) {{
                        console.log('Multiple refresh failures, falling back to full page reload');
                        window.location.reload();
                    }}
                }});
        }}
        
        // Set up smooth refresh every 10 seconds
        setInterval(refreshData, 10000);
        console.log('Smooth refresh enabled - updating every 10 seconds');
    }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(key_html))

def add_map_key(m, primary_node_id):
    key_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 140px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px;">
        &nbsp;<b>Key</b><br>
        &nbsp;<i class="fa fa-star" style="color:{COLOR_PRIMARY_NODE}"></i>&nbsp;{primary_node_id}<br>
        &nbsp;<i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_DAY}"></i>&nbsp;Seen in Last Day<br>
        &nbsp;<i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_WEEK}"></i>&nbsp;Seen in Last Week<br>
        &nbsp;<i class="fa fa-map-marker" style="color:{COLOR_SEEN_OVER_WEEK}"></i>&nbsp;Seen Over a Week Ago<br>
        &nbsp;<i class="fa fa-map-marker" style="color:{COLOR_NO_LAST_HEARD}"></i>&nbsp;No Last Heard
    </div>
    """
    m.get_root().html.add_child(folium.Element(key_html))

def add_sitrep_data(m):
    sitrep_time = mesh_data.get("sitrep_time", "N/A")
    sitrep_html = f"""
    <div id="sitrep" style="position: fixed; 
                top: 120px; right: 10px; width: 300px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <button onclick="document.getElementById('sitrep').style.display='none'">Minimize</button>
        <b>{sitrep_time} SITREP:</b><br>
    """
    for line in mesh_data["sitrep"][1:-1]:  # Exclude the first and last lines
        sitrep_html += f"&nbsp;{line}<br>"
    sitrep_html += "</div>"
    m.get_root().html.add_child(folium.Element(sitrep_html))

def add_nodes_without_position(m, nodes_without_position):
    nodes_without_position.sort(key=lambda x: (x['last_heard_time'].replace(tzinfo=None) if x['last_heard_time'] else datetime.min, x['hopsAway']), reverse=True)
    nodes_html = """
    <div id="nodes_without_position" style="position: fixed; 
                bottom: 10px; right: 10px; width: 400px; height: 200px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <button onclick="document.getElementById('nodes_without_position').style.display='none'">Minimize</button>
        <b>Nodes Without Position Data:</b><br>
        <div style="overflow-y: scroll; height: 150px;">
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr>
                        <th style="border: 1px solid black; padding: 5px;">Icon</th>
                        <th style="border: 1px solid black; padding: 5px;">ID</th>
                        <th style="border: 1px solid black; padding: 5px;">Heard</th>
                        <th style="border: 1px solid black; padding: 5px;">Hops</th>
                        <th style="border: 1px solid black; padding: 5px;">Connections</th>
                    </tr>
                </thead>
                <tbody>
    """
    for node in nodes_without_position:
        color = node['color']
        is_aircraft = node.get('is_aircraft', False)
        icon_class = 'fa-plane' if is_aircraft else 'fa-map-marker'
        hops_away_text = f"{node['hopsAway']}" if node['hopsAway'] != -1 else "N/A"
        connections = ", ".join(node['connections'])
        nodes_html += f"""
                    <tr>
                        <td style="border: 1px solid black; padding: 5px;"><i class='fa {icon_class}' style='color:{color}'></i></td>
                        <td style="border: 1px solid black; padding: 5px;">{node['id']}</td>
                        <td style="border: 1px solid black; padding: 5px;">{node['last_heard_str']}</td>
                        <td style="border: 1px solid black; padding: 5px;">{hops_away_text}</td>
                        <td style="border: 1px solid black; padding: 5px;">{connections}</td>
                    </tr>
        """
    nodes_html += """
                </tbody>
            </table>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(nodes_html))

def delete_old_maps():
    """Delete old map files to prevent accumulation"""
    logging.info("Cleaning up old map files.")
    try:
        import glob
        # Delete all existing map files
        map_files = glob.glob('templates/map_*.html')
        for map_file in map_files:
            try:
                os.remove(map_file)
                logging.debug(f"Deleted old map file: {map_file}")
            except FileNotFoundError:
                pass
        logging.info(f"Cleaned up {len(map_files)} old map files")
    except Exception as e:
        logging.error(f"Error cleaning up map files: {e}")

def update_map():
    delete_old_maps()
    read_mesh_data()
    m = create_map()

    unique_map_filename = f"map_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    m.save(f"templates/{unique_map_filename}")

    response = render_template(unique_map_filename)
    return response

class MeshDataHandler(FileSystemEventHandler):
    def on_modified(self, event):
        logging.info(f"Event type: {event.event_type}; Path: {event.src_path}")
        if event.src_path == MESH_DATA_FILE:
            logging.info("Mesh data file has changed.")

def monitor_data_updates():
    logging.info(f"Monitoring mesh data file: {MESH_DATA_FILE}")
    observer = Observer()
    event_handler = MeshDataHandler()
    observer.schedule(event_handler, path=os.path.dirname(MESH_DATA_FILE), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(10)  # Refresh data every 10 seconds
            logging.info("Checking for mesh data updates.")
            update_map()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

def background_refresh():
    """Background thread to refresh mesh data every 10 seconds"""
    while True:
        try:
            time.sleep(10)  # Refresh every 10 seconds
            logging.info("Background refresh: Reading mesh data...")
            read_mesh_data()
        except Exception as e:
            logging.error(f"Error in background refresh: {e}")

def start_background_refresh():
    """Start the background refresh thread"""
    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()
    logging.info("Background refresh thread started")

if __name__ == '__main__':
    logging.info("Starting Flask app with background refresh.")
    # Start background refresh thread
    start_background_refresh()
    # Start Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)