import json
import logging
import os
import time
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
COLOR_PRIMARY_NODE = 'white'
COLOR_SEEN_LAST_HOUR = 'green'
COLOR_SEEN_LAST_DAY = 'blue'
COLOR_SEEN_LAST_WEEK = 'orange'
COLOR_SEEN_OVER_WEEK = 'gray'
COLOR_NO_LAST_HEARD = 'red'
COLOR_CONNECTION_DEFAULT = 'green'
COLOR_CONNECTION_NON_PRIMARY = 'gray'
COLOR_PRECISION_CIRCLE = 'red'

# Sample .json data for mesh nodes
DEFAULT_MESH_DATA = {
    "last_update": "2024-04-23T00:00:00Z",
    "sitrep_time": "2024-04-23T00:00:00Z",
    "nodes": [
        {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "lastHeard": "", "connections": ["node2", "node3"]},
        {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "lastHeard": "1739400886",  "connections": ["node1"]},
        {"id": "node3", "lat": 0, "lon": 0, "alt": 0, "lastHeard": "1739400960",  "connections": ["node1"]}
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

@app.route('/filter_map')
def filter_map():
    """Create a filtered map based on age filter"""
    max_age_hours = request.args.get('max_age_hours', 168, type=float)
    logging.info(f"Filtering map with max age: {max_age_hours} hours")
    
    read_mesh_data()
    m = create_map(max_age_hours=max_age_hours)
    
    unique_map_filename = f"map_filtered_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
    m.save(f"templates/{unique_map_filename}")
    
    response = render_template(unique_map_filename)
    return response

def read_mesh_data():
    global mesh_data
    try:
        logging.info("Reading mesh data from file.")
        with open(MESH_DATA_FILE, 'r') as f:
            mesh_data = json.load(f)
        logging.info(f"Mesh data: {mesh_data}")
    except FileNotFoundError:
        logging.warning(f"Mesh data file not found. Using default data.")
        mesh_data = DEFAULT_MESH_DATA

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

def create_map(max_age_hours=168):
    main_node = mesh_data["nodes"][0]
    logging.info(f"Main node: {main_node}")
    main_node['alt'] += 100  # Add 100 meters to the primary node's altitude

    logging.info(f"Creating map centered around {main_node['id']} at {main_node['lat']}, {main_node['lon']} with age filter: {max_age_hours}h.")
    m = folium.Map(location=[main_node['lat'], main_node['lon']], zoom_start=12)

    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)

    nodes_without_position = []
    filtered_nodes_count = 0
    total_nodes_count = 0

    for node in mesh_data["nodes"][1:]:
        total_nodes_count += 1
        
        if node['lastHeard']:
            last_heard_time = datetime.fromtimestamp(int(node['lastHeard']), tz=timezone.utc)
            last_heard = time_since_last_heard(last_heard_time)
            age_hours = (now - last_heard_time).total_seconds() / 3600
        else:
            last_heard = "N/A"
            last_heard_time = None
            age_hours = float('inf')  # Treat nodes with no lastHeard as very old
            
        # Apply age filter here - skip nodes that are too old
        if max_age_hours < 168 and age_hours > max_age_hours:
            filtered_nodes_count += 1
            continue
            
        if last_heard_time:
            if last_heard_time > one_hour_ago:
                color = COLOR_SEEN_LAST_HOUR
            elif last_heard_time > one_day_ago:
                color = COLOR_SEEN_LAST_DAY    
            elif last_heard_time > one_week_ago:
                color = COLOR_SEEN_LAST_WEEK
            else:
                color = COLOR_SEEN_OVER_WEEK
        else:
            color = COLOR_NO_LAST_HEARD

        node['color'] = color
        node['last_heard_str'] = last_heard
        node['last_heard_time'] = last_heard_time

        if node['lat'] == 0 or node['lon'] == 0:
            nodes_without_position.append(node)
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

    # Add connections (only for nodes that passed the filter)
    for node in mesh_data["nodes"]:
        if node['lat'] == 0 or node['lon'] == 0:
            continue
            
        # Check if this node passed the age filter
        if node != main_node:  # Skip age check for main node
            if node['lastHeard']:
                last_heard_time = datetime.fromtimestamp(int(node['lastHeard']), tz=timezone.utc)
                age_hours = (now - last_heard_time).total_seconds() / 3600
            else:
                age_hours = float('inf')
            
            if max_age_hours < 168 and age_hours > max_age_hours:
                continue  # Skip connections for filtered out nodes
        
        for connection in node['connections']:
            connected_node = next((n for n in mesh_data["nodes"] if n['id'] == connection), None)
            if connected_node and connected_node['lat'] != 0 and connected_node['lon'] != 0:
                # Check if connected node also passed the filter
                if connected_node != main_node:  # Skip age check for main node
                    if connected_node['lastHeard']:
                        connected_last_heard = datetime.fromtimestamp(int(connected_node['lastHeard']), tz=timezone.utc)
                        connected_age_hours = (now - connected_last_heard).total_seconds() / 3600
                    else:
                        connected_age_hours = float('inf')
                    
                    if max_age_hours < 168 and connected_age_hours > max_age_hours:
                        continue  # Skip connection if target node is filtered out
                
                connection_color = COLOR_CONNECTION_DEFAULT if connection == main_node['id'] else COLOR_CONNECTION_NON_PRIMARY
                folium.PolyLine(
                    locations=[[node['lat'], node['lon']], [connected_node['lat'], connected_node['lon']]],
                    color=connection_color
                ).add_to(m)

    add_map_key(m, main_node['id'])
    add_age_filter_slider(m, max_age_hours, filtered_nodes_count, total_nodes_count)
    add_last_updated_label(m)
    add_sitrep_data(m)
    add_nodes_without_position(m, nodes_without_position)

    logging.info(f"Map created with {total_nodes_count - filtered_nodes_count} visible nodes, {filtered_nodes_count} filtered out")
    return m

def add_age_filter_slider(m, current_max_age=168, filtered_count=0, total_count=0):
    """Add a slider widget to filter nodes by age"""
    
    def update_age_display(hours):
        if hours >= 168:
            return 'All nodes (7+ days)'
        elif hours >= 24:
            days = int(hours // 24)
            return f'≤ {days} day{"s" if days > 1 else ""} old'
        elif hours >= 1:
            return f'≤ {int(hours)} hour{"s" if hours > 1 else ""} old'
        else:
            return 'Real-time only'
    
    current_display = update_age_display(current_max_age)
    if filtered_count > 0:
        current_display += f' (hiding {filtered_count} nodes)'
    
    slider_html = f"""
    <div id="age-filter" style="position: fixed; 
                top: 10px; left: 10px; width: 320px; height: 120px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <label for="ageSlider"><b>Filter by Node Age:</b></label><br>
        <input type="range" id="ageSlider" min="0" max="168" value="{current_max_age}" step="1" style="width: 220px;">
        <br>
        <span id="ageValue">{current_display}</span><br>
        <button id="resetFilter" style="margin-top: 5px; font-size: 12px;">Reset</button>
        <button id="hideFilter" style="margin-left: 5px; font-size: 12px;">Hide</button>
        <span style="font-size: 10px; color: gray;">Showing {total_count - filtered_count}/{total_count} nodes</span>
    </div>
    
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        const slider = document.getElementById('ageSlider');
        const ageValue = document.getElementById('ageValue');
        const resetButton = document.getElementById('resetFilter');
        const hideButton = document.getElementById('hideFilter');
        const filterDiv = document.getElementById('age-filter');
        
        function updateAgeDisplay(hours) {{
            if (hours >= 168) {{
                return 'All nodes (7+ days)';
            }} else if (hours >= 24) {{
                const days = Math.floor(hours / 24);
                return `≤ ${{days}} day${{days > 1 ? 's' : ''}} old`;
            }} else if (hours >= 1) {{
                return `≤ ${{hours}} hour${{hours > 1 ? 's' : ''}} old`;
            }} else {{
                return 'Real-time only';
            }}
        }}
        
        function applyFilter(maxAgeHours) {{
            console.log('Applying filter with max age:', maxAgeHours, 'hours');
            ageValue.textContent = updateAgeDisplay(maxAgeHours) + ' (loading...)';
            
            // Reload the page with the filter parameter
            const url = new URL('/filter_map', window.location.origin);
            url.searchParams.set('max_age_hours', maxAgeHours);
            window.location.href = url.toString();
        }}
        
        // Debounce slider input to avoid too many requests
        let sliderTimeout;
        slider.addEventListener('input', function() {{
            const hours = parseInt(this.value);
            ageValue.textContent = updateAgeDisplay(hours) + ' (loading...)';
            
            clearTimeout(sliderTimeout);
            sliderTimeout = setTimeout(() => {{
                applyFilter(hours);
            }}, 500); // Wait 500ms after user stops moving slider
        }});
        
        resetButton.addEventListener('click', function() {{
            applyFilter(168);
        }});
        
        hideButton.addEventListener('click', function() {{
            filterDiv.style.display = 'none';
            
            // Add a small show button
            const showButton = document.createElement('div');
            showButton.innerHTML = 'Show Filter';
            showButton.style.cssText = `
                position: fixed; top: 10px; left: 10px; 
                background-color: white; border: 2px solid grey; 
                z-index: 9999; font-size: 12px; padding: 5px; 
                cursor: pointer;
            `;
            showButton.onclick = function() {{
                filterDiv.style.display = 'block';
                document.body.removeChild(showButton);
            }};
            document.body.appendChild(showButton);
        }});
    }});
    </script>
    """
    m.get_root().html.add_child(folium.Element(slider_html))

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

def add_last_updated_label(m):
    last_updated = mesh_data.get("last_update", "N/A")
    logging.info(f"Adding last updated label to the map. Last updated: {last_updated}")
    last_updated_html = f"""
    <div style="position: fixed; 
                bottom: 10px; left: 50px; width: 250px; height: 30px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; white-space: nowrap;">
        &nbsp;Last Updated: {last_updated}
    </div>
    """
    m.get_root().html.add_child(folium.Element(last_updated_html))

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
        hops_away_text = f"{node['hopsAway']}" if node['hopsAway'] != -1 else "N/A"
        connections = ", ".join(node['connections'])
        nodes_html += f"""
                    <tr>
                        <td style="border: 1px solid black; padding: 5px;"><i class='fa fa-map-marker' style='color:{color}'></i></td>
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
    logging.info("Deleting existing map.")
    try:
        os.remove('templates/map_*.html')
    except FileNotFoundError:
        pass

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

if __name__ == '__main__':
    logging.info("Starting Flask app.")
    monitor_data_updates()
    app.run(debug=True)