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


def _circle_icon_svg(color_name: str, radius_px: int = 6) -> str:
    """Generate an inline SVG circle matching the CircleMarker style on the map.
    Returns an <svg> element sized to fit with matching fill and stroke color."""
    hex_c = COLOR_HEX.get(color_name, COLOR_HEX.get('gray', '#7B7B7B'))
    diam = max(radius_px * 2, 6)  # minimum 6px diameter for visibility in UI
    svg_r = diam // 2
    size = diam + 2  # 1px padding for stroke
    cx = cy = size // 2
    return (
        f'<svg width="{size}" height="{size}" style="vertical-align:middle;">'
        f'<circle cx="{cx}" cy="{cy}" r="{svg_r}" '
        f'fill="{hex_c}" stroke="{hex_c}" stroke-width="1.5" fill-opacity="0.85"/>'
        f'</svg>'
    )


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
                width: {MAP_KEY_POSITION['width']}; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px;">
        <b>Map Key</b><br>
        <div style="margin-top: 5px;">
            <div style="margin: 2px 0;">
                <i class="fa fa-star" style="color:{COLOR_PRIMARY_NODE}"></i>&nbsp;{primary_node_id} (Primary)
            </div>
            <div style="margin: 2px 0;">
                {_circle_icon_svg(COLOR_SEEN_LAST_HOUR, MARKER_SIZE_BY_AGE['last_hour'])}&nbsp;Last Hour
                &nbsp;{_circle_icon_svg(COLOR_SEEN_LAST_DAY, MARKER_SIZE_BY_AGE['last_day'])}&nbsp;Last Day
                &nbsp;{_circle_icon_svg(COLOR_SEEN_LAST_WEEK, MARKER_SIZE_BY_AGE['last_week'])}&nbsp;Last Week
            </div>
            <div style="margin: 2px 0;">
                {_circle_icon_svg(COLOR_SEEN_OVER_WEEK, MARKER_SIZE_BY_AGE['over_week'])}&nbsp;Older
                &nbsp;{_circle_icon_svg(COLOR_NO_LAST_HEARD, MARKER_SIZE_BY_AGE['no_last_heard'])}&nbsp;No Last Heard
            </div>
        </div>
        <div style="margin-top: 8px; border-top: 1px solid #ccc; padding-top: 5px;">
            <b style="font-size:12px;">Coverage &amp; Overlays</b>
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


def create_node_list_html(all_nodes: list, primary_node_id: str, visibility_settings: dict = None) -> str:
    """Generate HTML for the collapsible node list panel"""
    import json as _json

    # Determine active time filter from visibility settings
    if visibility_settings:
        # Figure out which cumulative level is active
        if visibility_settings.get('show_over_week') or visibility_settings.get('show_no_last_heard'):
            active_time = 'all'
        elif visibility_settings.get('show_last_week'):
            active_time = 'last_week'
        elif visibility_settings.get('show_last_day'):
            active_time = 'last_day'
        elif visibility_settings.get('show_last_hour'):
            active_time = 'last_hour'
        else:
            active_time = 'all'
    else:
        active_time = 'all'

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

    sidebar_w = NODE_LIST_SIDEBAR['width']
    html = f"""
    <style>
        #node-list-panel {{
            position: fixed; top: 0; left: 0; bottom: 0;
            width: {sidebar_w};
            background: white; border-right: 2px solid #ccc;
            z-index: 9998; font-size: 13px;
            display: flex; flex-direction: column;
            box-shadow: 2px 0 8px rgba(0,0,0,0.15);
        }}
        .folium-map {{
            margin-left: {sidebar_w} !important;
            width: calc(100% - {sidebar_w}) !important;
        }}
        #node-search-input {{
            width: 100%; border: 1px solid #ccc; border-radius: 4px;
            padding: 5px 8px 5px 28px; font-size: 13px; outline: none;
            box-sizing: border-box;
        }}
        #node-search-input:focus {{ border-color: #2196F3; }}
        #node-filter-section {{
            padding: 8px 10px; border-bottom: 1px solid #ddd;
            background: #fafafa; flex-shrink: 0;
        }}
        .node-filter-row {{
            display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap;
        }}
        .node-filter-chip {{
            font-size: 11px; padding: 2px 8px; border: 1px solid #ccc;
            border-radius: 12px; background: white; cursor: pointer;
            user-select: none; white-space: nowrap; transition: all 0.15s;
        }}
        .node-filter-chip:hover {{ border-color: #999; }}
        .node-filter-chip.active {{ background: #e3f2fd; border-color: #2196F3; color: #1565C0; }}
        #node-list-count {{ color: #888; font-size: 11px; margin-left: 4px; }}
        .time-filter-section {{
            padding: 6px 10px; border-bottom: 1px solid #ddd;
            background: #fafafa; flex-shrink: 0;
        }}
        .time-filter-section label {{
            font-size: 11px; font-weight: bold; color: #555; display: block; margin-bottom: 4px;
        }}
        .time-filter-row {{
            display: flex; gap: 4px; flex-wrap: wrap;
        }}
        .time-filter-chip {{
            font-size: 11px; padding: 3px 10px; border: 1px solid #ccc;
            border-radius: 12px; background: white; cursor: pointer;
            user-select: none; white-space: nowrap; transition: all 0.15s;
        }}
        .time-filter-chip:hover {{ border-color: #999; }}
        .time-filter-chip.active {{ background: #e8f5e9; border-color: #4CAF50; color: #2E7D32; }}
    </style>
    <div id="node-list-panel">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 12px;
             border-bottom:1px solid #ddd; background:#f8f8f8; flex-shrink:0;">
            <span><b>\\U0001f4e1 Nodes ({len(sorted_nodes)})</b><span id="node-list-count"></span></span>
        </div>
        <div id="node-filter-section">
            <div style="position:relative;">
                <i class="fa fa-search" style="position:absolute; left:8px; top:7px; color:#999; font-size:12px;"></i>
                <input id="node-search-input" type="text" placeholder="Search nodes...">
            </div>
            <div class="node-filter-row">
                <span class="node-filter-chip active" data-filter="all" onclick="window._applyFilter('all',this)">All</span>
                <span class="node-filter-chip" data-filter="has-position" onclick="window._applyFilter('has-position',this)">Has Position</span>
                <span class="node-filter-chip" data-filter="no-position" onclick="window._applyFilter('no-position',this)">No Position</span>
                <span class="node-filter-chip" data-filter="direct" onclick="window._applyFilter('direct',this)">Direct (0-1 hop)</span>
            </div>
        </div>
        <div class="time-filter-section">
            <label>\\U0001f552 Time Filter</label>
            <div class="time-filter-row">
                <span class="time-filter-chip{' active' if active_time == 'last_hour' else ''}" data-time="last_hour" onclick="window._applyTimeFilter('last_hour',this)">Last Hour</span>
                <span class="time-filter-chip{' active' if active_time == 'last_day' else ''}" data-time="last_day" onclick="window._applyTimeFilter('last_day',this)">Last Day</span>
                <span class="time-filter-chip{' active' if active_time == 'last_week' else ''}" data-time="last_week" onclick="window._applyTimeFilter('last_week',this)">Last Week</span>
                <span class="time-filter-chip{' active' if active_time == 'all' else ''}" data-time="all" onclick="window._applyTimeFilter('all',this)">All Time</span>
            </div>
        </div>
        <div id="node-list-body" style="overflow-y:auto; flex:1; padding:4px 0;">
            <table style="width:100%; border-collapse:collapse;">
    """

    for node in sorted_nodes:
        color = COLOR_PRIMARY_NODE if node.id == primary_node_id else node.color
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
        hops_val = 0 if node.id == primary_node_id else (node.hops_away if node.hops_away >= 0 else 99)
        age = node.age_group if node.id != primary_node_id else 'primary'

        # Use star icon for primary, circle icons matching map markers for others
        if node.id == primary_node_id:
            icon_td = f'<i class="fa fa-star" style="color:{COLOR_HEX.get(color, color)}"></i>'
        else:
            marker_r = MARKER_SIZE_BY_AGE.get(age, MARKER_SIZE_BY_AGE['over_week'])
            icon_td = _circle_icon_svg(color, min(marker_r, 8))

        html += f"""
                <tr class="node-row" data-node-id="{node.id}" data-has-pos="{'1' if has_pos else '0'}" data-hops="{hops_val}" data-age="{age}"
                    {click_handler} style="border-bottom:1px solid #eee;{cursor}{opacity}" {hover}>
                    <td style="padding:4px 6px; width:20px; text-align:center;">{icon_td}</td>
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

    # Add search, filter, and click-to-locate JS
    html += f"""
    <script>
    window._nodeListPositions = {_json.dumps(node_positions)};

    /* ---------- Locate on map ---------- */
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

    /* ---------- Filter state ---------- */
    window._activeFilter = 'all';
    window._activeTimeFilter = '{active_time}';

    /* ---------- Age groups included at each cumulative level ---------- */
    window._timeFilterGroups = {{
        'last_hour': ['last_hour'],
        'last_day':  ['last_hour', 'last_day'],
        'last_week': ['last_hour', 'last_day', 'last_week'],
        'all':       ['last_hour', 'last_day', 'last_week', 'over_week', 'no_last_heard', 'primary']
    }};

    window._applyFilter = function(filter, chip) {{
        window._activeFilter = filter;
        document.querySelectorAll('.node-filter-chip').forEach(function(c) {{ c.classList.remove('active'); }});
        if (chip) chip.classList.add('active');
        window._filterNodeList();
    }};

    /* ---------- Time filter — triggers server reload for map ---------- */
    window._applyTimeFilter = function(timeLevel, chip) {{
        // Save map view before reload
        if (window.meshMapController) window.meshMapController._saveMapView();

        // Build the visibility settings for the server
        var url = new URL('/filter_map', window.location.origin);

        // Carry over non-time visibility settings from current page
        var vs = window.visibilitySettings || {{}};
        url.searchParams.set('show_receive_range', (vs.show_receive_range || false).toString());
        url.searchParams.set('show_receive_range_1hop', (vs.show_receive_range_1hop || false).toString());
        url.searchParams.set('show_receive_range_2hop', (vs.show_receive_range_2hop || false).toString());
        url.searchParams.set('show_receive_range_3hop', (vs.show_receive_range_3hop || false).toString());
        url.searchParams.set('show_range_rings', (vs.show_range_rings !== false).toString());

        // Set cumulative time visibility
        var groups = window._timeFilterGroups[timeLevel] || window._timeFilterGroups['all'];
        url.searchParams.set('show_last_hour', groups.includes('last_hour').toString());
        url.searchParams.set('show_last_day', groups.includes('last_day').toString());
        url.searchParams.set('show_last_week', groups.includes('last_week').toString());
        url.searchParams.set('show_over_week', groups.includes('over_week').toString());
        url.searchParams.set('show_no_last_heard', groups.includes('no_last_heard').toString());

        window.location.href = url.toString();
    }};

    /* ---------- Combined search + property + time filter ---------- */
    window._filterNodeList = function() {{
        var query = (document.getElementById('node-search-input').value || '').trim().toUpperCase();
        var filter = window._activeFilter;
        var timeFilter = window._activeTimeFilter;
        var allowedAges = window._timeFilterGroups[timeFilter] || window._timeFilterGroups['all'];
        var rows = document.querySelectorAll('.node-row');
        var shown = 0;
        rows.forEach(function(row) {{
            var nodeId = row.getAttribute('data-node-id') || '';
            var hasPos = row.getAttribute('data-has-pos') === '1';
            var hops = parseInt(row.getAttribute('data-hops') || '99', 10);
            var age = row.getAttribute('data-age') || '';
            var matchSearch = !query || nodeId.toUpperCase().indexOf(query) !== -1;
            var matchFilter = true;
            if (filter === 'has-position') matchFilter = hasPos;
            else if (filter === 'no-position') matchFilter = !hasPos;
            else if (filter === 'direct') matchFilter = hops <= 1;
            var matchTime = allowedAges.indexOf(age) !== -1;
            row.style.display = (matchSearch && matchFilter && matchTime) ? '' : 'none';
            if (matchSearch && matchFilter && matchTime) shown++;
        }});
        var countEl = document.getElementById('node-list-count');
        if (countEl) {{
            if (query || filter !== 'all' || timeFilter !== 'all') {{
                countEl.textContent = ' (showing ' + shown + ')';
            }} else {{
                countEl.textContent = '';
            }}
        }}
    }};

    /* ---------- Search input listeners ---------- */
    (function() {{
        var input = document.getElementById('node-search-input');
        if (!input) return;
        input.addEventListener('input', function() {{ window._filterNodeList(); }});
        input.addEventListener('keydown', function(e) {{
            if (e.key === 'Enter') {{
                e.preventDefault();
                // On Enter, also locate first visible node on the map
                var firstVisible = document.querySelector('.node-row[style=""], .node-row:not([style*="display: none"])');
                if (firstVisible) {{
                    var nid = firstVisible.getAttribute('data-node-id');
                    if (nid) window._locateNode(nid);
                }}
            }}
        }});
        // Apply initial filter on load (so time filter is reflected in the list)
        window._filterNodeList();
    }})();
    </script>
    """

    return html
