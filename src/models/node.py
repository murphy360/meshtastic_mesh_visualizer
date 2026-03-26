"""
Node model and related functionality
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config.settings import AIRCRAFT_ALTITUDE_THRESHOLD
from config.colors import AGE_GROUP_COLORS, COLOR_NO_LAST_HEARD


class MeshNode:
    """Represents a single mesh node with its properties and state"""
    
    def __init__(self, node_data: Dict[str, Any]):
        self.id = node_data.get('id', '')
        self.lat = node_data.get('lat', 0.0)
        self.lon = node_data.get('lon', 0.0)
        self.alt = node_data.get('alt', 0)
        self.last_heard = node_data.get('lastHeard', '')
        self.hops_away = node_data.get('hopsAway', -1)
        self.connections = node_data.get('connections', [])
        self.precision_bits = node_data.get('precision_bits')
        
        # Computed properties
        self._last_heard_time = None
        self._age_group = None
        self._color = None
        self._is_aircraft = None
        
    @property
    def last_heard_time(self) -> Optional[datetime]:
        """Get the last heard time as a datetime object"""
        if self._last_heard_time is None and self.last_heard:
            try:
                self._last_heard_time = datetime.fromtimestamp(int(self.last_heard), tz=timezone.utc)
            except (ValueError, TypeError):
                self._last_heard_time = None
        return self._last_heard_time
    
    @property
    def is_aircraft(self) -> bool:
        """Determine if this node represents an aircraft"""
        if self._is_aircraft is None:
            self._is_aircraft = self.alt > AIRCRAFT_ALTITUDE_THRESHOLD
        return self._is_aircraft
    
    @property
    def has_valid_position(self) -> bool:
        """Check if the node has valid position data"""
        return self.lat != 0 and self.lon != 0
    
    @property
    def age_group(self) -> str:
        """Get the age group based on last heard time"""
        if self._age_group is None:
            from utils.time_utils import get_age_group
            self._age_group = get_age_group(self.last_heard_time)
        return self._age_group
    
    @property
    def color(self) -> str:
        """Get the color for this node based on its age group"""
        if self._color is None:
            self._color = AGE_GROUP_COLORS.get(self.age_group, COLOR_NO_LAST_HEARD)
        return self._color
    
    def should_show(self, visibility_settings: Dict[str, bool]) -> bool:
        """Determine if this node should be visible based on settings"""
        setting_key = f'show_{self.age_group}'
        return visibility_settings.get(setting_key, True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary representation"""
        return {
            'id': self.id,
            'lat': self.lat,
            'lon': self.lon,
            'alt': self.alt,
            'lastHeard': self.last_heard,
            'hopsAway': self.hops_away,
            'connections': self.connections,
            'precision_bits': self.precision_bits
        }
