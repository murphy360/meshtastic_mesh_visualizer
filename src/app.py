import json
import logging
import os
import time
import folium
from datetime import datetime, timezone, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from flask import Flask, render_template, make_response

# Configure logging
logging.basicConfig(format='%(asctime)s - %(filename)s:%(lineno)d - %(message)s', level=logging.INFO)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching of static files

MESH_DATA_FILE = os.getenv('MESH_DATA_FILE', '/data/mesh_data.json')

# Define color variables
COLOR_PRIMARY_NODE = 'green'
COLOR_SEEN_LAST_DAY = 'blue'
COLOR_SEEN_LAST_WEEK = 'orange'
COLOR_SEEN_OVER_WEEK = 'gray'
COLOR_NO_LAST_HEARD = 'red'
COLOR_CONNECTION_DEFAULT = 'green'
COLOR_CONNECTION_NON_PRIMARY = 'gray'

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

def create_map():
    main_node = mesh_data["nodes"][0]
    logging.info(f"Main node: {main_node}")
    main_node['alt'] += 100  # Add 100 meters to the primary node's altitude

    logging.info(f"Creating map centered around {main_node['id']} at {main_node['lat']}, {main_node['lon']}.")
    m = folium.Map(location=[main_node['lat'], main_node['lon']], zoom_start=12)

    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(days=1)
    one_week_ago = now - timedelta(weeks=1)

    nodes_without_position = []

    for node in mesh_data["nodes"][1:]:

        if node['lastHeard']:
            #logging.info(f"Node {node['id']} was last heard at {node['lastHeard']}")
            last_heard_time = datetime.fromtimestamp(int(node['lastHeard']), tz=timezone.utc)
            last_heard = time_since_last_heard(last_heard_time)
        else:
            #logging.warning(f"Node {node['id']} has no last heard data.")
            last_heard = "N/A"
            last_heard_time = None
            
        if last_heard_time:
            if last_heard_time > one_day_ago:
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
            #logging.warning(f"Node {node['id']} does not have position data.")
            nodes_without_position.append(node)
        else:
            #logging.info(f"Adding marker for {node['id']} at {node['lat']}, {node['lon']} with color {color}.")
            icon = folium.Icon(color=color)
            popup_text = f"{node['id']}<br>Altitude: {node['alt']}m<br>Last Heard: {last_heard}"
            if node.get('hopsAway', 0) != 0:
                popup_text += f"<br>Hops Away: {node['hopsAway']}"
            folium.Marker(
                location=[node['lat'], node['lon']],
                popup=popup_text,
                icon=icon
            ).add_to(m)

    icon = folium.Icon(color=COLOR_PRIMARY_NODE, icon='star', prefix='fa')
    folium.Marker(
        location=[main_node['lat'], main_node['lon']],
        popup=f"{main_node['id']}<br>Altitude: {main_node['alt']}m",
        icon=icon
    ).add_to(m)

    for node in mesh_data["nodes"]:
        if node['lat'] == 0 or node['lon'] == 0:
            continue
        for connection in node['connections']:
            connected_node = next((n for n in mesh_data["nodes"] if n['id'] == connection), None)
            if connected_node and connected_node['lat'] != 0 and connected_node['lon'] != 0:
                connection_color = COLOR_CONNECTION_DEFAULT if connection == main_node['id'] else COLOR_CONNECTION_NON_PRIMARY
                folium.PolyLine(
                    locations=[[node['lat'], node['lon']], [connected_node['lat'], connected_node['lon']]],
                    color=connection_color
                ).add_to(m)

    add_map_key(m, main_node['id'])
    add_last_updated_label(m)
    add_sitrep_data(m)
    add_nodes_without_position(m, nodes_without_position)

    return m

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
                top: 10px; right: 10px; width: 300px; height: auto; 
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