import json
import logging
import os
import folium


from flask import Flask, render_template

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)

app = Flask(__name__)

# Sample data for mesh nodes
mesh_data = [
    {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "connections": ["node2", "node3"]},
    {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "connections": ["node1"]},
    {"id": "node3", "lat": 37.6879, "lon": -122.4702, "alt": 15, "connections": ["node1"]}
]

@app.route('/')
def index():

    # Read mesh data from a JSON file
    try:
        logging.info("Reading mesh data from file.")
        with open('/data/mesh_data.json', 'r') as f:
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

    # Save the map to an HTML file
    m.save('templates/map.html')
    return render_template('map.html')

# List directory contents
logging.info("Listing directory contents.")
logging.info(os.listdir())

if __name__ == '__main__':
    logging.info("Starting Flask app.")
    app.run(debug=True)