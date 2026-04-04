"""
Map service for creating and managing Folium maps
"""
import folium
import logging
import glob
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from models.mesh_data import MeshData
from models.node import MeshNode
from config.settings import *
from config.colors import *
from services.polygon_service import PolygonService
from utils.time_utils import time_since_last_heard, get_time_thresholds
from utils.geo_utils import calculate_precision_radius
from utils.template_utils import (
    create_interactive_map_key_html,
    create_sitrep_html,
    create_node_list_html
)


class MapService:
    """Service for creating and managing Folium maps"""
    
    def __init__(self):
        self.polygon_service = PolygonService()
    
    def create_map(self, mesh_data: MeshData, visibility_settings: Optional[Dict[str, bool]] = None) -> folium.Map:
        """Create a Folium map with all nodes, connections, and overlays"""
        
        # Use default visibility settings if none provided
        if visibility_settings is None:
            visibility_settings = DEFAULT_VISIBILITY_SETTINGS.copy()
        
        primary_node = mesh_data.primary_node
        if not primary_node:
            raise ValueError("No primary node found in mesh data")
        
        # Adjust primary node altitude
        primary_node.alt += PRIMARY_NODE_ALTITUDE_OFFSET
        
        logging.info(f"Creating map centered around {primary_node.id} at {primary_node.lat}, {primary_node.lon} with visibility: {visibility_settings}")
        
        # Create the base map
        m = folium.Map(
            location=[primary_node.lat, primary_node.lon],
            zoom_start=MAP_ZOOM_START
        )
        
        # Get time thresholds for age calculations
        time_thresholds = get_time_thresholds()
        
        # Process and add nodes
        filtered_nodes_count = 0
        total_nodes_count = 0
        age_group_counts = mesh_data.get_age_group_counts()
        
        # Add secondary nodes
        for node in mesh_data.secondary_nodes:
            total_nodes_count += 1
            
            # Check visibility
            if not node.should_show(visibility_settings):
                filtered_nodes_count += 1
                continue
            
            if node.has_valid_position:
                self._add_node_to_map(m, node, time_thresholds, visibility_settings)
        
        # Always add the primary node
        self._add_primary_node_to_map(m, primary_node, time_thresholds, visibility_settings)
        
        # Add connections
        self._add_connections_to_map(m, mesh_data, visibility_settings, time_thresholds)
        
        # Add polygon overlays
        self._add_polygon_overlays(m, mesh_data, visibility_settings)
        
        # Add UI elements
        self._add_interactive_map_key(m, primary_node.id, visibility_settings, age_group_counts, mesh_data.last_update)
        self._add_sitrep_data(m, mesh_data)
        self._add_node_list_panel(m, mesh_data, visibility_settings)
        
        logging.info(f"Map created with {total_nodes_count - filtered_nodes_count} visible nodes, {filtered_nodes_count} filtered out")
        return m
    
    def _add_node_to_map(self, m: folium.Map, node: MeshNode, time_thresholds: Dict[str, datetime], visibility_settings: Optional[Dict[str, bool]] = None) -> None:
        """Add a node marker to the map"""
        if visibility_settings is None:
            visibility_settings = DEFAULT_VISIBILITY_SETTINGS.copy()
        last_heard_str = time_since_last_heard(node.last_heard_time) if node.last_heard_time else "N/A"
        
        # Build popup text
        if node.is_aircraft:
            popup_text = f"✈️ {node.id} (Aircraft)<br>Altitude: {node.alt}m<br>Last Heard: {last_heard_str}"
        elif node.is_infrastructure:
            logging.info(f"Infrastructure node detected: {node.id} (role={node.role})")
            popup_text = f"🖧 {node.id} (Router)<br>Altitude: {node.alt}m<br>Last Heard: {last_heard_str}"
        else:
            popup_text = f"{node.id}<br>Altitude: {node.alt}m<br>Last Heard: {last_heard_str}"
        
        if node.hops_away != 0:
            popup_text += f"<br>Hops Away: {node.hops_away}"
        
        # Add precision info if available
        if node.precision_bits:
            logging.info(f"Node {node.id} has precision bits: {node.precision_bits}")
            popup_text += f"<br>Precision: {node.precision_bits} bits"
        
        # Determine age-based marker size
        age = node.age_group
        radius = MARKER_SIZE_BY_AGE.get(age, MARKER_SIZE_BY_AGE['over_week'])
        hex_color = COLOR_HEX.get(node.color, '#7B7B7B')
        
        # Pick a FontAwesome icon label for the tooltip
        if node.is_aircraft:
            icon_char = '✈'
        elif node.is_infrastructure:
            icon_char = '⛳'
        else:
            icon_char = '●'
        
        # Use CircleMarker for all age groups — size reflects recency
        marker = folium.CircleMarker(
            location=[node.lat, node.lon],
            radius=radius,
            color=hex_color,
            fill=True,
            fill_color=hex_color,
            fill_opacity=0.85 if age == 'last_hour' else 0.7 if age == 'last_day' else 0.5,
            weight=1,
            popup=popup_text,
            tooltip=f"{icon_char} {node.id}"
        )
        marker.add_to(m)
        
        # Add precision circle if available and enabled in visibility settings
        if visibility_settings.get('show_range_rings', True) and node.precision_bits:
            radius = calculate_precision_radius(node.precision_bits)
            if radius and radius > 0:
                folium.Circle(
                    location=[node.lat, node.lon],
                    radius=radius,
                    color=COLOR_PRECISION_CIRCLE,
                    fill=True,
                    fill_opacity=0.1,
                    popup=popup_text
                ).add_to(m)
    
    def _add_primary_node_to_map(self, m: folium.Map, primary_node: MeshNode, time_thresholds: Dict[str, datetime], visibility_settings: Optional[Dict[str, bool]] = None) -> None:
        """Add the primary node with special styling"""
        if visibility_settings is None:
            visibility_settings = DEFAULT_VISIBILITY_SETTINGS.copy()
        icon = folium.Icon(color=COLOR_PRIMARY_NODE, icon='star', prefix='fa')
        popup_lines = [
            f"\u2b50 {primary_node.id} (Primary)",
            f"Altitude: {primary_node.alt}m",
        ]
        if primary_node.connections:
            popup_lines.append(f"Connections: {len(primary_node.connections)}")
        popup_text = "<br>".join(popup_lines)
        
        marker = folium.Marker(
            location=[primary_node.lat, primary_node.lon],
            popup=popup_text,
            icon=icon
        )
        marker.add_to(m)
        
        # Add precision circle for primary node if available and enabled in visibility settings
        if visibility_settings.get('show_range_rings', True) and primary_node.precision_bits:
            radius = calculate_precision_radius(primary_node.precision_bits)
            if radius and radius > 0:
                folium.Circle(
                    location=[primary_node.lat, primary_node.lon],
                    radius=radius,
                    color=COLOR_PRECISION_CIRCLE,
                    fill=True,
                    fill_opacity=0.1,
                    popup=popup_text + f"<br>Precision: {primary_node.precision_bits} bits"
                ).add_to(m)
    
    def _add_connections_to_map(
        self, 
        m: folium.Map, 
        mesh_data: MeshData, 
        visibility_settings: Dict[str, bool],
        time_thresholds: Dict[str, datetime]
    ) -> None:
        """Add connection lines between nodes"""
        primary_node = mesh_data.primary_node
        
        for node in mesh_data.nodes:
            if not node.has_valid_position:
                continue
            
            # Check if this node is visible
            if node != primary_node and not node.should_show(visibility_settings):
                continue
            
            for connection_id in node.connections:
                connected_node = next((n for n in mesh_data.nodes if n.id == connection_id), None)
                if not connected_node or not connected_node.has_valid_position:
                    continue
                
                # Check if connected node is also visible
                if connected_node != primary_node and not connected_node.should_show(visibility_settings):
                    continue
                
                connection_color = COLOR_CONNECTION_DEFAULT if connection_id == primary_node.id else COLOR_CONNECTION_NON_PRIMARY
                folium.PolyLine(
                    locations=[[node.lat, node.lon], [connected_node.lat, connected_node.lon]],
                    color=connection_color
                ).add_to(m)
    
    def _add_polygon_overlays(self, m: folium.Map, mesh_data: MeshData, visibility_settings: Dict[str, bool]) -> None:
        """Add polygon overlays for different hop ranges"""
        for hop_count in range(4):  # 0, 1, 2, 3 hops
            setting_key = 'show_receive_range' if hop_count == 0 else f'show_receive_range_{hop_count}hop'
            
            if visibility_settings.get(setting_key, False):
                polygon_coords = self.polygon_service.create_receive_range_polygon(
                    mesh_data, visibility_settings, hop_count
                )
                
                if polygon_coords:
                    color = HOP_RANGE_COLORS[hop_count]
                    opacity = HOP_RANGE_OPACITY[hop_count]
                    
                    if hop_count == 0:
                        popup_text = "Direct Receive Range (0-hop nodes only)"
                    else:
                        popup_text = f"{hop_count}-Hop Network Range (0-{hop_count} hop nodes)"
                    
                    folium.Polygon(
                        locations=polygon_coords,
                        color=color,
                        weight=3,
                        fill=True,
                        fillColor=color,
                        fillOpacity=opacity,
                        popup=popup_text
                    ).add_to(m)
                else:
                    logging.info(f"Not enough visible {hop_count}-hop nodes to create receive range polygon")
    
    def _add_interactive_map_key(
        self, 
        m: folium.Map, 
        primary_node_id: str, 
        visibility_settings: Dict[str, bool], 
        age_group_counts: Dict[str, int],
        last_update: str
    ) -> None:
        """Add the interactive map key with JavaScript functionality"""
        key_html = create_interactive_map_key_html(
            primary_node_id, visibility_settings, age_group_counts, last_update
        )
        
        # Embed JavaScript directly instead of referencing external file
        js_code = f"""
        <script>
        // Set visibility settings for JavaScript
        window.visibilitySettings = {str(visibility_settings).replace('True', 'true').replace('False', 'false')};
        
        /**
         * Interactive map functionality for mesh visualizer
         */
        class MeshMapController {{
            constructor(visibilitySettings) {{
                this.visibilitySettings = visibilitySettings;
                this.lastDataHash = null;
                this.refreshFailures = 0;
                this.init();
            }}

            init() {{
                this.setupToggleListeners();
                this.startRefreshInterval();
                this.restoreMapView();
            }}

            // Find the Leaflet map instance from the Folium-generated page
            _getLeafletMap() {{
                const mapEl = document.querySelector('.folium-map');
                if (mapEl && mapEl._leaflet_id) {{
                    // Access Leaflet's internal map registry
                    for (const key of Object.keys(window)) {{
                        const val = window[key];
                        if (val && val._container === mapEl) return val;
                    }}
                }}
                return null;
            }}

            // Save current map center/zoom to sessionStorage before navigating away
            _saveMapView() {{
                const map = this._getLeafletMap();
                if (map) {{
                    const center = map.getCenter();
                    sessionStorage.setItem('meshMapView', JSON.stringify({{
                        lat: center.lat, lng: center.lng, zoom: map.getZoom()
                    }}));
                }}
            }}

            // Restore map center/zoom from sessionStorage after page load
            restoreMapView() {{
                const saved = sessionStorage.getItem('meshMapView');
                // Small delay to let Folium finish initializing
                setTimeout(() => {{
                    const map = this._getLeafletMap();
                    if (map) {{
                        // Notify Leaflet the container size changed (sidebar layout)
                        map.invalidateSize();
                        if (saved) {{
                            try {{
                                const view = JSON.parse(saved);
                                map.setView([view.lat, view.lng], view.zoom);
                                console.log('Restored map view:', view);
                            }} catch (e) {{
                                console.warn('Could not restore map view:', e);
                            }}
                        }}
                    }}
                }}, 100);
            }}

            setupToggleListeners() {{
                // Coverage polygon toggles
                document.getElementById('toggle-receive-range')?.addEventListener('click', () => {{
                    this.toggleVisibility('receive_range', this.visibilitySettings.show_receive_range);
                }});

                document.getElementById('toggle-receive-range-1hop')?.addEventListener('click', () => {{
                    this.toggleVisibility('receive_range_1hop', this.visibilitySettings.show_receive_range_1hop);
                }});

                document.getElementById('toggle-receive-range-2hop')?.addEventListener('click', () => {{
                    this.toggleVisibility('receive_range_2hop', this.visibilitySettings.show_receive_range_2hop);
                }});

                document.getElementById('toggle-receive-range-3hop')?.addEventListener('click', () => {{
                    this.toggleVisibility('receive_range_3hop', this.visibilitySettings.show_receive_range_3hop);
                }});

                // Range rings toggle
                document.getElementById('toggle-range-rings')?.addEventListener('click', () => {{
                    this.toggleVisibility('range_rings', this.visibilitySettings.show_range_rings);
                }});
            }}

            toggleVisibility(group, currentState) {{
                console.log('Toggling visibility for group:', group, 'current state:', currentState);
                this._saveMapView();
                
                // Build URL with toggled state
                const url = new URL('/filter_map', window.location.origin);
                const newState = !currentState;
                
                // Set all current visibility states
                for (const [key, value] of Object.entries(this.visibilitySettings)) {{
                    url.searchParams.set(key, value.toString());
                }}
                
                // Toggle the specific group
                url.searchParams.set('show_' + group, newState.toString());
                
                console.log('Navigating to:', url.toString());
                window.location.href = url.toString();
            }}

            startRefreshInterval() {{
                // Set up smooth refresh every 10 seconds
                setInterval(() => this.refreshData(), 10000);
                console.log('Smooth refresh enabled - updating every 10 seconds');
            }}

            _showUpdateIndicator() {{
                let indicator = document.getElementById('mesh-update-indicator');
                if (!indicator) {{
                    indicator = document.createElement('div');
                    indicator.id = 'mesh-update-indicator';
                    indicator.style.cssText = 'position:fixed;top:10px;left:50%;transform:translateX(-50%);background:#2196F3;color:white;padding:8px 20px;border-radius:4px;z-index:10000;font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.3);transition:opacity 0.3s;';
                    document.body.appendChild(indicator);
                }}
                indicator.textContent = 'Updating map...';
                indicator.style.opacity = '1';
            }}

            async refreshData() {{
                try {{
                    const response = await fetch('/get_mesh_data');
                    const data = await response.json();
                    
                    // Update the last updated timestamp in the key
                    const lastUpdatedElement = document.getElementById('last-updated-timestamp');
                    if (lastUpdatedElement) {{
                        lastUpdatedElement.textContent = 'Last Updated: ' + data.last_update;
                    }}
                    
                    // Check if actual node data has changed using hash
                    if (this.lastDataHash !== null && this.lastDataHash !== data.data_hash) {{
                        console.log('Node data changed, reloading map. Hash changed from', this.lastDataHash, 'to', data.data_hash);
                        this._saveMapView();
                        this._showUpdateIndicator();
                        window.location.reload();
                        return;
                    }}
                    
                    // Store the current hash for future comparisons
                    this.lastDataHash = data.data_hash;
                    
                    console.log('Data refreshed at:', data.timestamp, 'Hash:', data.data_hash);
                    // Reset failure counter on success
                    this.refreshFailures = 0;
                    
                }} catch (error) {{
                    console.error('Error refreshing data:', error);
                    // Fall back to full page refresh if data fetch fails after 3 failures
                    this.refreshFailures++;
                    if (this.refreshFailures >= 3) {{
                        console.log('Multiple refresh failures, falling back to full page reload');
                        this._saveMapView();
                        window.location.reload();
                    }}
                }}
            }}
        }}

        // Initialize when DOM is loaded
        document.addEventListener('DOMContentLoaded', function() {{
            // This will be populated by the template
            window.meshMapController = new MeshMapController(window.visibilitySettings);
        }});
        </script>
        """
        
        combined_html = key_html + js_code
        m.get_root().html.add_child(folium.Element(combined_html))
    
    def _add_node_list_panel(self, m: folium.Map, mesh_data: MeshData, visibility_settings: Dict[str, bool]) -> None:
        """Add a collapsible node list panel to the map"""
        # Include ALL nodes in the list — time filtering is done client-side
        all_nodes = [mesh_data.primary_node] if mesh_data.primary_node else []
        all_nodes.extend(mesh_data.secondary_nodes)
        
        primary_id = mesh_data.primary_node.id if mesh_data.primary_node else ""
        node_list_html = create_node_list_html(all_nodes, primary_id, visibility_settings)
        m.get_root().html.add_child(folium.Element(node_list_html))
    
    def _add_sitrep_data(self, m: folium.Map, mesh_data: MeshData) -> None:
        """Add SITREP data display"""
        sitrep_html = create_sitrep_html(mesh_data.sitrep_time, mesh_data.sitrep)
        m.get_root().html.add_child(folium.Element(sitrep_html))
    
    @staticmethod
    def delete_old_maps() -> None:
        """Delete old map files to prevent accumulation"""
        logging.info("Cleaning up old map files.")
        try:
            # Get the correct path to templates directory relative to src/
            templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
            templates_path = os.path.abspath(templates_dir)
            pattern = os.path.join(templates_path, 'map_*.html')
            
            # Delete all existing map files
            map_files = glob.glob(pattern)
            for map_file in map_files:
                try:
                    os.remove(map_file)
                    logging.debug(f"Deleted old map file: {map_file}")
                except FileNotFoundError:
                    pass
            logging.info(f"Cleaned up {len(map_files)} old map files")
        except Exception as e:
            logging.error(f"Error cleaning up map files: {e}")
    
    def save_map(self, m: folium.Map, prefix: str = "map") -> str:
        """Save map to file and return filename"""
        unique_map_filename = f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}.html"
        # Get the correct path to templates directory relative to src/
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
        templates_path = os.path.abspath(templates_dir)
        full_path = os.path.join(templates_path, unique_map_filename)
        m.save(full_path)
        return unique_map_filename


# Global instance
map_service = MapService()
