import json
import logging
import os
import folium
from datetime import datetime

from flask import Flask, render_template

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

# Get the path to the mesh data file from the environment variable
MESH_DATA_FILE = os.getenv('MESH_DATA_FILE', '/data/mesh_data.json')

# Sample data for mesh nodes
mesh_data = [
    {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "connections": ["node2", "node3"]},
    {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "connections": ["node1"]},
    {"id": "node3", "lat": 37.6879, "lon": -122.4702, "alt": 15, "connections": ["node1"]}
]

@app.route('/')
def index():
    update_map()
    return render_template('map.html')

def update_map():
    global mesh_data
    # Read mesh data from a JSON file
    try:
        logging.info("Reading mesh data from file.")
        with open(MESH_DATA_FILE, 'r') as f:
            mesh_data = json.load(f)
        logging.info(f"Mesh data: {mesh_data}")
    except FileNotFoundError:
        print("File not found. Using sample data.")
        mesh_data = [
            {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "connections": ["node2", "node3"]},
            {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "connections": ["node1"]},
            {"id": "node3", "lat": 37.6879, "lon": -122.4702, "alt": 15, "connections": ["node1"]}
        ]

    # Create a map centered around the first node
    main_node = mesh_data[0]
    main_node['alt'] += 100  # Add 100 meters to the primary node's altitude
    logging.info(f"Creating map centered around {main_node['id']} at {main_node['lat']}, {main_node['lon']}.")
    m = folium.Map(location=[main_node['lat'], main_node['lon']], zoom_start=12)

    # Add non-primary nodes to the map first
    for i, node in enumerate(mesh_data[1:], start=1):
        if not node['connections']:
            icon = folium.Icon(color='red', icon='exclamation-sign', prefix='glyphicon')  # Node with no connections
        else:
            icon = folium.Icon(color='blue')
        folium.Marker(
            location=[node['lat'], node['lon']],
            popup=f"Node ID: {node['id']}<br>Altitude: {node['alt']}m",
            icon=icon
        ).add_to(m)

    # Add the primary node last
    icon = folium.Icon(color='green', icon='star', prefix='fa')  # Primary node with a star icon
    folium.Marker(
        location=[main_node['lat'], main_node['lon']],
        popup=f"Node ID: {main_node['id']}<br>Altitude: {main_node['alt']}m",
        icon=icon
    ).add_to(m)

    # Draw lines between direct connections
    for node in mesh_data:
        for connection in node['connections']:
            connected_node = next((n for n in mesh_data if n['id'] == connection), None)
            if connected_node:
                folium.PolyLine(
                    locations=[[node['lat'], node['lon']], [connected_node['lat'], connected_node['lon']]], 
                    color='green'
                ).add_to(m)

    # Add a key to the map
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

    # Add a "Last Updated" label to the map
    last_updated = datetime.now().strftime('%Y-%m-%d %H:%M')
    last_updated_html = f"""
    <div style="position: fixed; 
                bottom: 10px; left: 50px; width: 250px; height: 30px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; white-space: nowrap;">
        &nbsp;Last Updated: {last_updated}
    </div>
    """
    m.get_root().html.add_child(folium.Element(last_updated_html))

    # Save the map to an HTML file
    m.save('templates/map.html')
    return render_template('map.html')

if __name__ == '__main__':
    logging.info("Starting Flask app.")
    app.run(debug=True)