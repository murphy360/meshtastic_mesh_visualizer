import json
import logging
import os
import time
import folium
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from flask import Flask, render_template, make_response

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching of static files

MESH_DATA_FILE = os.getenv('MESH_DATA_FILE', '/data/mesh_data.json')

# Sample .json data for mesh nodes
DEFAULT_MESH_DATA = {
    "last_update": "2024-04-23T00:00:00Z",
    "nodes": [
        {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "connections": ["node2", "node3"]},
        {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "connections": ["node1"]},
        {"id": "node3", "lat": 37.6879, "lon": -122.4702, "alt": 15, "connections": ["node1"]}
    ]
}

mesh_data = DEFAULT_MESH_DATA

@app.route('/')
def index():
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

def create_map():
    main_node = mesh_data["nodes"][0]
    main_node['alt'] += 100  # Add 100 meters to the primary node's altitude

    logging.info(f"Creating map centered around {main_node['id']} at {main_node['lat']}, {main_node['lon']}.")
    m = folium.Map(location=[main_node['lat'], main_node['lon']], zoom_start=12)

    for node in mesh_data["nodes"][1:]:
        icon = folium.Icon(color='red', icon='exclamation-sign', prefix='glyphicon') if not node['connections'] else folium.Icon(color='blue')
        folium.Marker(
            location=[node['lat'], node['lon']],
            popup=f"Node ID: {node['id']}<br>Altitude: {node['alt']}m",
            icon=icon
        ).add_to(m)

    icon = folium.Icon(color='green', icon='star', prefix='fa')
    folium.Marker(
        location=[main_node['lat'], main_node['lon']],
        popup=f"Node ID: {main_node['id']}<br>Altitude: {main_node['alt']}m",
        icon=icon
    ).add_to(m)

    for node in mesh_data["nodes"]:
        for connection in node['connections']:
            connected_node = next((n for n in mesh_data["nodes"] if n['id'] == connection), None)
            if connected_node:
                folium.PolyLine(
                    locations=[[node['lat'], node['lon']], [connected_node['lat'], connected_node['lon']]],
                    color='green'
                ).add_to(m)

    add_map_key(m)
    add_last_updated_label(m)

    return m

def add_map_key(m):
    key_html = """
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 150px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px;">
        &nbsp;<b>Key</b><br>
        &nbsp;<i class="fa fa-star" style="color:green"></i>&nbsp;Primary Node<br>
        &nbsp;<i class="glyphicon glyphicon-exclamation-sign" style="color:red"></i>&nbsp;No Connections<br>
        &nbsp;<i class="fa fa-map-marker" style="color:blue"></i>&nbsp;Connected Node
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