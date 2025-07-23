"""
Data service for reading and managing mesh data
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any
from config.settings import MESH_DATA_FILE
from models.mesh_data import MeshData


# Default mesh data
DEFAULT_MESH_DATA = {
    "last_update": "2024-04-23T00:00:00Z",
    "sitrep_time": "2024-04-23T00:00:00Z",
    "nodes": [
        {"id": "node1", "lat": 37.7749, "lon": -122.4194, "alt": 10, "lastHeard": "", "hopsAway": 0, "connections": ["node2", "node3"]},
        {"id": "node2", "lat": 37.8044, "lon": -122.2711, "alt": 20, "lastHeard": "1739400886", "hopsAway": 0, "connections": ["node1"]},
        {"id": "node3", "lat": 0, "lon": 0, "alt": 0, "lastHeard": "1739400960", "hopsAway": 1, "connections": ["node1"]},
        {"id": "node4", "lat": 37.7849, "lon": -122.4094, "alt": 15, "lastHeard": "1739400800", "hopsAway": 0, "connections": ["node1"]},
        {"id": "node5", "lat": 37.7649, "lon": -122.4294, "alt": 25, "lastHeard": "1739400900", "hopsAway": 0, "connections": ["node1"]},
        {"id": "node6", "lat": 37.7549, "lon": -122.4394, "alt": 30, "lastHeard": "1739400800", "hopsAway": 1, "connections": ["node2"]},
        {"id": "node7", "lat": 37.7949, "lon": -122.4594, "alt": 35, "lastHeard": "1739400850", "hopsAway": 1, "connections": ["node4"]},
        {"id": "node8", "lat": 37.7349, "lon": -122.3994, "alt": 40, "lastHeard": "1739400750", "hopsAway": 2, "connections": ["node6"]},
        {"id": "node9", "lat": 37.8149, "lon": -122.4794, "alt": 45, "lastHeard": "1739400780", "hopsAway": 2, "connections": ["node7"]},
        {"id": "node10", "lat": 37.7449, "lon": -122.4494, "alt": 50, "lastHeard": "1739400820", "hopsAway": 2, "connections": ["node6"]},
        {"id": "node11", "lat": 37.7149, "lon": -122.3794, "alt": 55, "lastHeard": "1739400700", "hopsAway": 3, "connections": ["node8"]},
        {"id": "node12", "lat": 37.8349, "lon": -122.4994, "alt": 60, "lastHeard": "1739400730", "hopsAway": 3, "connections": ["node9"]},
        {"id": "node13", "lat": 37.7249, "lon": -122.4694, "alt": 65, "lastHeard": "1739400760", "hopsAway": 3, "connections": ["node10"]}
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


class DataService:
    """Service for managing mesh data operations"""
    
    def __init__(self):
        self._current_data = MeshData(DEFAULT_MESH_DATA)
        self._current_data.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    @property
    def current_data(self) -> MeshData:
        """Get the current mesh data"""
        return self._current_data
    
    def read_mesh_data(self) -> MeshData:
        """Read mesh data from file and update current data"""
        try:
            logging.info(f"Reading mesh data from file: {MESH_DATA_FILE}")
            with open(MESH_DATA_FILE, 'r') as f:
                new_data_dict = json.load(f)
            
            new_mesh_data = MeshData(new_data_dict)
            
            # Check if data has changed
            if self._current_data.to_dict() != new_mesh_data.to_dict():
                logging.info("Mesh data has changed, updating...")
                self._current_data = new_mesh_data
            else:
                logging.debug("Mesh data unchanged")
            
            # Always update the last_update timestamp to show when we last checked
            self._current_data.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
                
            logging.debug(f"Current mesh data timestamp: {self._current_data.last_update}")
            
        except FileNotFoundError:
            logging.warning(f"Mesh data file not found at {MESH_DATA_FILE}. Using default data.")
            self._current_data = MeshData(DEFAULT_MESH_DATA)
            self._current_data.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing mesh data JSON: {e}. Using default data.")
            self._current_data = MeshData(DEFAULT_MESH_DATA)
            self._current_data.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            
        except Exception as e:
            logging.error(f"Unexpected error reading mesh data: {e}. Using default data.")
            self._current_data = MeshData(DEFAULT_MESH_DATA)
            self._current_data.last_update = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        
        return self._current_data
    
    def get_mesh_data_summary(self) -> Dict[str, Any]:
        """Get a summary of current mesh data for API responses"""
        return {
            "last_update": self._current_data.last_update,
            "nodes": [node.to_dict() for node in self._current_data.nodes],
            "node_count": len(self._current_data.nodes),
            "data_hash": self._current_data.get_data_hash(),
            "timestamp": datetime.now().isoformat()
        }


# Global instance
data_service = DataService()
