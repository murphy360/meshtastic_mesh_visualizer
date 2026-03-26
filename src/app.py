"""
Flask application for Meshtastic mesh visualizer
Refactored for better modularity and maintainability
"""
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify

# Configure logging
logging.basicConfig(format='%(asctime)s - %(filename)s:%(lineno)d - %(message)s', level=logging.INFO)

# Import our services and utilities
from services.data_service import data_service
from services.map_service import map_service
from services.file_monitor import FileMonitorService
from config.settings import DEFAULT_VISIBILITY_SETTINGS

# Initialize Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching of static files

# Initialize file monitor service
file_monitor_service = FileMonitorService(data_service)


@app.route('/')
def index():
    """Main page - display the mesh map"""
    logging.info("Request received for index.")
    return update_map()


@app.route('/refresh')
def refresh_data():
    """Manual refresh endpoint"""
    logging.info("Manual refresh requested")
    data_service.read_mesh_data()
    return jsonify({"status": "refreshed", "timestamp": datetime.now().isoformat()})


@app.route('/get_mesh_data')
def get_mesh_data_endpoint():
    """Return current mesh data as JSON for live updates"""
    data_service.read_mesh_data()
    return jsonify(data_service.get_mesh_data_summary())


@app.route('/filter_map')
def filter_map():
    """Create a filtered map based on visibility toggles"""
    # Parse visibility parameters from request
    visibility_settings = parse_visibility_settings(request.args)
    
    logging.info(f"Filtering map with visibility settings: {visibility_settings}")
    
    # Read latest data and create map
    mesh_data = data_service.read_mesh_data()
    m = map_service.create_map(mesh_data, visibility_settings)
    
    # Save and serve the map
    filename = map_service.save_map(m, "map_filtered")
    return render_template(filename)


def parse_visibility_settings(args) -> dict:
    """Parse visibility settings from request arguments"""
    return {
        'show_last_hour': args.get('show_last_hour', 'true').lower() == 'true',
        'show_last_day': args.get('show_last_day', 'true').lower() == 'true',
        'show_last_week': args.get('show_last_week', 'true').lower() == 'true',
        'show_over_week': args.get('show_over_week', 'true').lower() == 'true',
        'show_no_last_heard': args.get('show_no_last_heard', 'true').lower() == 'true',
        'show_receive_range': args.get('show_receive_range', 'false').lower() == 'true',
        'show_receive_range_1hop': args.get('show_receive_range_1hop', 'false').lower() == 'true',
        'show_receive_range_2hop': args.get('show_receive_range_2hop', 'false').lower() == 'true',
        'show_receive_range_3hop': args.get('show_receive_range_3hop', 'false').lower() == 'true',
        'show_range_rings': args.get('show_range_rings', 'true').lower() == 'true',
    }


def update_map():
    """Update and serve the main map"""
    map_service.delete_old_maps()
    mesh_data = data_service.read_mesh_data()
    m = map_service.create_map(mesh_data, DEFAULT_VISIBILITY_SETTINGS)
    
    filename = map_service.save_map(m, "map")
    return render_template(filename)


if __name__ == '__main__':
    logging.info("Starting Flask app with background refresh.")
    
    # Start background services
    file_monitor_service.start_background_refresh()
    
    try:
        # Start Flask app
        app.run(debug=True, host='0.0.0.0', port=5000)
    finally:
        # Clean up background services
        file_monitor_service.stop_background_refresh()
        file_monitor_service.stop_file_monitor()
