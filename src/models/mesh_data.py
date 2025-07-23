"""
Mesh data model and validation
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from models.node import MeshNode


class MeshData:
    """Represents the complete mesh network data"""
    
    def __init__(self, data: Dict[str, Any]):
        self.last_update = data.get('last_update', 'N/A')
        self.sitrep_time = data.get('sitrep_time', 'N/A')
        self.sitrep = data.get('sitrep', [])
        
        # Convert node data to MeshNode objects
        self.nodes = [MeshNode(node_data) for node_data in data.get('nodes', [])]
        
    @property
    def primary_node(self) -> Optional[MeshNode]:
        """Get the primary (first) node"""
        return self.nodes[0] if self.nodes else None
    
    @property
    def secondary_nodes(self) -> List[MeshNode]:
        """Get all nodes except the primary node"""
        return self.nodes[1:] if len(self.nodes) > 1 else []
    
    def get_nodes_with_position(self) -> List[MeshNode]:
        """Get all nodes that have valid position data"""
        return [node for node in self.nodes if node.has_valid_position]
    
    def get_nodes_without_position(self) -> List[MeshNode]:
        """Get all nodes that don't have valid position data"""
        return [node for node in self.nodes if not node.has_valid_position]
    
    def get_visible_nodes(self, visibility_settings: Dict[str, bool]) -> List[MeshNode]:
        """Get all nodes that should be visible based on settings"""
        visible_nodes = []
        for node in self.nodes:
            if node == self.primary_node:  # Primary node is always visible
                visible_nodes.append(node)
            elif node.should_show(visibility_settings):
                visible_nodes.append(node)
        return visible_nodes
    
    def get_age_group_counts(self) -> Dict[str, int]:
        """Get count of nodes in each age group"""
        counts = {
            'last_hour': 0,
            'last_day': 0,
            'last_week': 0,
            'over_week': 0,
            'no_last_heard': 0
        }
        
        for node in self.secondary_nodes:  # Exclude primary node from counts
            age_group = node.age_group
            if age_group in counts:
                counts[age_group] += 1
                
        return counts
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert mesh data to dictionary representation"""
        return {
            'last_update': self.last_update,
            'sitrep_time': self.sitrep_time,
            'sitrep': self.sitrep,
            'nodes': [node.to_dict() for node in self.nodes]
        }
    
    def get_data_hash(self) -> int:
        """Get a hash of the node data for change detection"""
        node_data_str = str([node.to_dict() for node in self.nodes])
        return hash(node_data_str)
