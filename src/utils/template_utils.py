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
                bottom: {MAP_KEY_POSITION['bottom']}; right: {MAP_KEY_POSITION['right']}; 
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


def create_node_list_html(all_nodes: list, primary_node_id: str) -> str:
    """Generate HTML for the collapsible node list panel"""
    import json as _json

    # Sort: primary first, then by last heard (most recent first), then by hops
    def sort_key(node):
        if node.id == primary_node_id:
            return (0, datetime.max, 0)
        heard = node.last_heard_time.replace(tzinfo=None) if node.last_heard_time else datetime.min
        return (1, heard, node.hops_away if node.hops_away >= 0 else 999)

    sorted_nodes = sorted(all_nodes, key=sort_key, reverse=False)
    # Reverse the non-primary nodes so most-recent is first
    primary = [n for n in sorted_nodes if n.id == primary_node_id]
    others = sorted(
        [n for n in sorted_nodes if n.id != primary_node_id],
        key=lambda n: (
            n.last_heard_time.replace(tzinfo=None) if n.last_heard_time else datetime.min,
            -(n.hops_away if n.hops_away >= 0 else 999)
        ),
        reverse=True
    )
    sorted_nodes = primary + others

    # Build node lookup for click-to-locate
    node_positions = {}
    for node in sorted_nodes:
        if node.has_valid_position:
            node_positions[node.id] = [node.lat, node.lon]

    pos = NODE_LIST_POSITION
    html = f"""
    <div id="node-list-panel" style="position:fixed; top:{pos['top']}; left:{pos['left']};
         width:{pos['width']}; max-height:{pos['max_height']}; background:white; border:2px solid grey;
         z-index:9998; font-size:13px; border-radius:4px; box-shadow:0 2px 8px rgba(0,0,0,0.2);
         display:flex; flex-direction:column;">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 10px;
             border-bottom:1px solid #ddd; background:#f8f8f8; border-radius:4px 4px 0 0;">
            <b>\U0001f4e1 Nodes ({len(sorted_nodes)})</b>
            <button id="node-list-toggle" onclick="
                var body=document.getElementById('node-list-body');
                var btn=this;
                if(body.style.display==='none'){{body.style.display='block';btn.textContent='\u25BC';}}
                else{{body.style.display='none';btn.textContent='\u25B6';}}
            " style="border:1px solid #ccc; border-radius:3px; background:white; cursor:pointer;
                    padding:2px 6px; font-size:12px;">\u25BC</button>
        </div>
        <div id="node-list-body" style="overflow-y:auto; padding:4px 0;">
            <table style="width:100%; border-collapse:collapse;">
    """

    for node in sorted_nodes:
        color = COLOR_PRIMARY_NODE if node.id == primary_node_id else node.color
        icon_class = 'fa-star' if node.id == primary_node_id else _get_node_icon_class(node)
        last_heard_str = time_since_last_heard(node.last_heard_time) if node.last_heard_time else "N/A"
        hops_text = "—" if node.id == primary_node_id else (str(node.hops_away) if node.hops_away >= 0 else "?")
        has_pos = node.has_valid_position
        cursor = "cursor:pointer;" if has_pos else ""
        click_handler = f"onclick=\"window._locateNode('{node.id}')\"" if has_pos else ""
        if has_pos:
            hover = 'onmouseover="this.style.background=\'#f0f7ff\'" onmouseout="this.style.background=\'\'"'
        else:
            hover = ''
        opacity = "" if has_pos else "opacity:0.55;"
        no_pos_badge = "" if has_pos else " <span style='color:#aaa;font-size:10px;' title='No position data'>&#x26AB;</span>"

        html += f"""
                <tr {click_handler} style="border-bottom:1px solid #eee;{cursor}{opacity}" {hover}>
                    <td style="padding:4px 6px; width:20px;"><i class="fa {icon_class}" style="color:{color}"></i></td>
                    <td style="padding:4px 4px; font-weight:{'bold' if node.id == primary_node_id else 'normal'};">{node.id}{no_pos_badge}</td>
                    <td style="padding:4px 6px; color:#888; font-size:11px; text-align:right; white-space:nowrap;">{last_heard_str}</td>
                    <td style="padding:4px 6px; color:#888; font-size:11px; text-align:center; width:30px;" title="Hops">{hops_text}</td>
                </tr>
        """

    html += """
            </table>
        </div>
    </div>
    """

    # Add click-to-locate JS
    html += f"""
    <script>
    window._nodeListPositions = {_json.dumps(node_positions)};
    window._locateNode = function(nodeId) {{
        var pos = window._nodeListPositions[nodeId];
        if (!pos) return;
        var mapEl = document.querySelector('.folium-map');
        if (!mapEl) return;
        for (var key of Object.keys(window)) {{
            var val = window[key];
            if (val && val._container === mapEl && typeof val.setView === 'function') {{
                val.setView([pos[0], pos[1]], 15);
                break;
            }}
        }}
    }};
    </script>
    """

    return html
