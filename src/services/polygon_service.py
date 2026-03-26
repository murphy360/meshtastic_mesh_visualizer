"""
Polygon service for creating mesh coverage polygons
"""
import logging
from typing import List, Optional, Dict, Any
from models.mesh_data import MeshData
from models.node import MeshNode
from utils.geo_utils import create_polygon_from_nodes


class PolygonService:
    """Service for creating and managing coverage polygons"""
    
    @staticmethod
    def create_receive_range_polygon(
        mesh_data: MeshData,
        visibility_settings: Dict[str, bool],
        hop_count: int = 0
    ) -> Optional[List[List[float]]]:
        """
        Create a polygon around all nodes with hop count <= specified value to show network range
        Only includes nodes that are currently visible based on visibility settings
        
        Args:
            mesh_data: The mesh data containing all nodes
            visibility_settings: Current visibility settings
            hop_count: Maximum number of hops away from primary node (0, 1, 2, etc.)
                      Includes all nodes with hops <= this value
                      
        Returns:
            List of [lat, lon] coordinate pairs forming the polygon, or None if insufficient points
        """
        primary_node = mesh_data.primary_node
        if not primary_node:
            return None
        
        # Get all nodes with hop count <= specified hop count that have valid positions and are currently visible
        hop_nodes = []
        
        for node in mesh_data.nodes:
            if (node.hops_away <= hop_count and 
                node.hops_away >= 0 and  # Ensure valid hop count
                node.has_valid_position and 
                node != primary_node):  # Exclude the main node itself
                
                # Check if this node would be visible based on age and visibility settings
                if node.should_show(visibility_settings):
                    hop_nodes.append((node.lat, node.lon))
        
        # Include the main node in all polygons (always visible and always 0 hops)
        if primary_node.has_valid_position:
            hop_nodes.append((primary_node.lat, primary_node.lon))
        
        if len(hop_nodes) < 3:
            # Need at least 3 points to create a polygon
            return None
        
        try:
            polygon_coords = create_polygon_from_nodes(hop_nodes)
            if polygon_coords:
                logging.info(f"Created {hop_count}-hop receive range polygon with {len(polygon_coords)} points")
            return polygon_coords
        except Exception as e:
            logging.warning(f"Could not create receive range polygon for {hop_count}-hop nodes: {e}")
            return None
