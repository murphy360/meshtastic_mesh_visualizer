"""
Template and HTML generation utilities
"""
from datetime import datetime
from typing import Dict, Any
from config.colors import *
from config.settings import *
from utils.time_utils import time_since_last_heard


def _get_node_icon_class(node) -> str:
    """Get the Font Awesome icon class for a node based on its type"""
    if node.is_aircraft:
        return f'fa-{ICON_AIRCRAFT}'
    elif node.is_infrastructure:
        return f'fa-{ICON_INFRASTRUCTURE}'
    return 'fa-map-marker'


def create_interactive_map_key_html(
    primary_node_id: str,
    visibility_settings: Dict[str, bool],
    age_group_counts: Dict[str, int],
    last_update: str
) -> str:
    """Generate HTML for the interactive map key"""
    
    def get_visibility_indicator(is_visible: bool) -> str:
        return "👁️" if is_visible else "❌"
    
    def get_opacity_style(is_visible: bool) -> str:
        return "opacity: 1.0;" if is_visible else "opacity: 0.5; text-decoration: line-through;"
    
    # Calculate visible node count
    visible_count = sum(
        count for key, count in age_group_counts.items() 
        if visibility_settings.get(f'show_{key}', True)
    )
    total_count = sum(age_group_counts.values())
    
    key_html = f"""
    <div style="position: fixed; 
                bottom: {MAP_KEY_POSITION['bottom']}; left: {MAP_KEY_POSITION['left']}; 
                width: {MAP_KEY_POSITION['width']}; height: {MAP_KEY_POSITION['height']}; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <b>Key - Click to Toggle Visibility</b><br>
        <div style="margin-top: 5px;">
            <div style="margin: 2px 0;">
                <span style="font-size: 12px;">👁️</span>
                <i class="fa fa-star" style="color:{COLOR_PRIMARY_NODE}"></i>&nbsp;{primary_node_id} (Always visible)
            </div>
            <div style="margin: 2px 0;">
                <span style="font-size: 12px;">ℹ️</span>
                <i class="fa fa-{ICON_INFRASTRUCTURE}" style="color:{COLOR_SEEN_LAST_HOUR}"></i>&nbsp;Router / Infrastructure Node
            </div>
            <div id="toggle-last-hour" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_last_hour'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_last_hour'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_HOUR}"></i>&nbsp;Last Hour ({age_group_counts['last_hour']})
            </div>
            <div id="toggle-last-day" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_last_day'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_last_day'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_DAY}"></i>&nbsp;Last Day ({age_group_counts['last_day']})
            </div>
            <div id="toggle-last-week" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_last_week'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_last_week'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_LAST_WEEK}"></i>&nbsp;Last Week ({age_group_counts['last_week']})
            </div>
            <div id="toggle-over-week" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_over_week'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_over_week'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_SEEN_OVER_WEEK}"></i>&nbsp;Over Week Ago ({age_group_counts['over_week']})
            </div>
            <div id="toggle-no-last-heard" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings['show_no_last_heard'])}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings['show_no_last_heard'])}</span>
                <i class="fa fa-map-marker" style="color:{COLOR_NO_LAST_HEARD}"></i>&nbsp;No Last Heard ({age_group_counts['no_last_heard']})
            </div>
        </div>
        <div style="margin-top: 8px; border-top: 1px solid #ccc; padding-top: 5px;">
            <div id="toggle-receive-range" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings.get('show_receive_range', False))}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings.get('show_receive_range', False))}</span>
                <i class="fa fa-circle-o" style="color:{COLOR_RECEIVE_RANGE}"></i>&nbsp;0-Hop Coverage (direct only)
            </div>
            <div id="toggle-receive-range-1hop" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings.get('show_receive_range_1hop', False))}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings.get('show_receive_range_1hop', False))}</span>
                <i class="fa fa-circle-o" style="color:{COLOR_RECEIVE_RANGE_1HOP}"></i>&nbsp;1-Hop Coverage (0-1 hops)
            </div>
            <div id="toggle-receive-range-2hop" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings.get('show_receive_range_2hop', False))}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings.get('show_receive_range_2hop', False))}</span>
                <i class="fa fa-circle-o" style="color:{COLOR_RECEIVE_RANGE_2HOP}"></i>&nbsp;2-Hop Coverage (0-2 hops)
            </div>
            <div id="toggle-receive-range-3hop" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings.get('show_receive_range_3hop', False))}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings.get('show_receive_range_3hop', False))}</span>
                <i class="fa fa-circle-o" style="color:{COLOR_RECEIVE_RANGE_3HOP}"></i>&nbsp;3-Hop Coverage (0-3 hops)
            </div>
            <div id="toggle-range-rings" style="margin: 2px 0; cursor: pointer; {get_opacity_style(visibility_settings.get('show_range_rings', True))}">
                <span style="font-size: 12px;">{get_visibility_indicator(visibility_settings.get('show_range_rings', True))}</span>
                <i class="fa fa-circle-o" style="color:{COLOR_PRECISION_CIRCLE}"></i>&nbsp;Range Rings - Position Precision
            </div>
            <div style="font-size: 10px; color: gray; margin-left: 15px;">
                Red circles show GPS precision uncertainty<br>
                Shown only for nodes heard within last day
            </div>
        </div>
        <div style="margin-top: 8px; font-size: 11px; color: gray;">
            Visible: {visible_count} / {total_count} nodes
        </div>
        <div style="margin-top: 5px; font-size: 10px; color: gray; border-top: 1px solid #eee; padding-top: 3px;" id="last-updated-timestamp">
            Last Updated: {last_update}
        </div>
    </div>
    """
    
    return key_html


def create_sitrep_html(sitrep_time: str, sitrep_lines: list) -> str:
    """Generate HTML for the SITREP display"""
    sitrep_html = f"""
    <div id="sitrep" style="position: fixed; 
                top: {SITREP_POSITION['top']}; right: {SITREP_POSITION['right']}; 
                width: {SITREP_POSITION['width']}; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <button onclick="document.getElementById('sitrep').style.display='none'">Minimize</button>
        <b>{sitrep_time} SITREP:</b><br>
    """
    for line in sitrep_lines[1:-1]:  # Exclude the first and last lines
        sitrep_html += f"&nbsp;{line}<br>"
    sitrep_html += "</div>"
    return sitrep_html


def create_nodes_without_position_html(nodes_without_position: list) -> str:
    """Generate HTML for the nodes without position display"""
    # Sort nodes by last heard time and hops away
    sorted_nodes = sorted(
        nodes_without_position,
        key=lambda x: (
            x.last_heard_time.replace(tzinfo=None) if x.last_heard_time else datetime.min,
            x.hops_away
        ),
        reverse=True
    )
    
    nodes_html = f"""
    <div id="nodes_without_position" style="position: fixed; 
                bottom: {NODES_WITHOUT_POSITION_CONFIG['bottom']}; right: {NODES_WITHOUT_POSITION_CONFIG['right']}; 
                width: {NODES_WITHOUT_POSITION_CONFIG['width']}; height: {NODES_WITHOUT_POSITION_CONFIG['height']}; 
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
    
    for node in sorted_nodes:
        
        color = node.color
        icon_class = _get_node_icon_class(node)
        hops_away_text = f"{node.hops_away}" if node.hops_away != -1 else "N/A"
        connections = ", ".join(node.connections)
        last_heard_str = time_since_last_heard(node.last_heard_time) if node.last_heard_time else "N/A"
        
        nodes_html += f"""
                    <tr>
                        <td style="border: 1px solid black; padding: 5px;"><i class='fa {icon_class}' style='color:{color}'></i></td>
                        <td style="border: 1px solid black; padding: 5px;">{node.id}</td>
                        <td style="border: 1px solid black; padding: 5px;">{last_heard_str}</td>
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
    return nodes_html
