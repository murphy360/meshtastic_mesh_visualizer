/**
 * Interactive map functionality for mesh visualizer
 */

class MeshMapController {
    constructor(visibilitySettings) {
        this.visibilitySettings = visibilitySettings;
        this.lastDataHash = null;
        this.refreshFailures = 0;
        this.init();
    }

    init() {
        this.setupToggleListeners();
        this.startRefreshInterval();
    }

    setupToggleListeners() {
        // Age group toggles
        document.getElementById('toggle-last-hour')?.addEventListener('click', () => {
            this.toggleVisibility('last_hour', this.visibilitySettings.show_last_hour);
        });

        document.getElementById('toggle-last-day')?.addEventListener('click', () => {
            this.toggleVisibility('last_day', this.visibilitySettings.show_last_day);
        });

        document.getElementById('toggle-last-week')?.addEventListener('click', () => {
            this.toggleVisibility('last_week', this.visibilitySettings.show_last_week);
        });

        document.getElementById('toggle-over-week')?.addEventListener('click', () => {
            this.toggleVisibility('over_week', this.visibilitySettings.show_over_week);
        });

        document.getElementById('toggle-no-last-heard')?.addEventListener('click', () => {
            this.toggleVisibility('no_last_heard', this.visibilitySettings.show_no_last_heard);
        });

        // Coverage polygon toggles
        document.getElementById('toggle-receive-range')?.addEventListener('click', () => {
            this.toggleVisibility('receive_range', this.visibilitySettings.show_receive_range);
        });

        document.getElementById('toggle-receive-range-1hop')?.addEventListener('click', () => {
            this.toggleVisibility('receive_range_1hop', this.visibilitySettings.show_receive_range_1hop);
        });

        document.getElementById('toggle-receive-range-2hop')?.addEventListener('click', () => {
            this.toggleVisibility('receive_range_2hop', this.visibilitySettings.show_receive_range_2hop);
        });

        document.getElementById('toggle-receive-range-3hop')?.addEventListener('click', () => {
            this.toggleVisibility('receive_range_3hop', this.visibilitySettings.show_receive_range_3hop);
        });
    }

    toggleVisibility(group, currentState) {
        console.log('Toggling visibility for group:', group, 'current state:', currentState);
        
        // Build URL with toggled state
        const url = new URL('/filter_map', window.location.origin);
        const newState = !currentState;
        
        // Set all current visibility states
        for (const [key, value] of Object.entries(this.visibilitySettings)) {
            url.searchParams.set(key, value.toString());
        }
        
        // Toggle the specific group
        url.searchParams.set('show_' + group, newState.toString());
        
        console.log('Navigating to:', url.toString());
        window.location.href = url.toString();
    }

    startRefreshInterval() {
        // Set up smooth refresh every 10 seconds
        setInterval(() => this.refreshData(), 10000);
        console.log('Smooth refresh enabled - updating every 10 seconds');
    }

    async refreshData() {
        try {
            const response = await fetch('/get_mesh_data');
            const data = await response.json();
            
            // Update the last updated timestamp in the key
            const lastUpdatedElement = document.getElementById('last-updated-timestamp');
            if (lastUpdatedElement) {
                lastUpdatedElement.textContent = 'Last Updated: ' + data.last_update;
            }
            
            // Check if actual node data has changed using hash
            if (this.lastDataHash !== null && this.lastDataHash !== data.data_hash) {
                console.log('Node data changed, reloading map. Hash changed from', this.lastDataHash, 'to', data.data_hash);
                window.location.reload();
                return;
            }
            
            // Store the current hash for future comparisons
            this.lastDataHash = data.data_hash;
            
            console.log('Data refreshed at:', data.timestamp, 'Hash:', data.data_hash);
            // Reset failure counter on success
            this.refreshFailures = 0;
            
        } catch (error) {
            console.error('Error refreshing data:', error);
            // Fall back to full page refresh if data fetch fails after 3 failures
            this.refreshFailures++;
            if (this.refreshFailures >= 3) {
                console.log('Multiple refresh failures, falling back to full page reload');
                window.location.reload();
            }
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // This will be populated by the template
    window.meshMapController = new MeshMapController(window.visibilitySettings);
});
