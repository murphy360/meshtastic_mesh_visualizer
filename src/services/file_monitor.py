"""
File monitoring service for mesh data updates
"""
import logging
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config.settings import MESH_DATA_FILE, REFRESH_INTERVAL_SECONDS


class MeshDataHandler(FileSystemEventHandler):
    """File system event handler for mesh data changes"""
    
    def on_modified(self, event):
        logging.info(f"Event type: {event.event_type}; Path: {event.src_path}")
        if event.src_path == MESH_DATA_FILE:
            logging.info("Mesh data file has changed.")


class FileMonitorService:
    """Service for monitoring file changes and background refresh"""
    
    def __init__(self, data_service):
        self.data_service = data_service
        self.observer = None
        self.refresh_thread = None
        self._stop_refresh = threading.Event()
    
    def start_file_monitor(self):
        """Start monitoring the mesh data file for changes"""
        logging.info(f"Monitoring mesh data file: {MESH_DATA_FILE}")
        self.observer = Observer()
        event_handler = MeshDataHandler()
        self.observer.schedule(event_handler, path=os.path.dirname(MESH_DATA_FILE), recursive=False)
        self.observer.start()
        return self.observer
    
    def stop_file_monitor(self):
        """Stop file monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
    
    def start_background_refresh(self):
        """Start the background refresh thread"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            return  # Already running
        
        self._stop_refresh.clear()
        self.refresh_thread = threading.Thread(target=self._background_refresh_loop, daemon=True)
        self.refresh_thread.start()
        logging.info("Background refresh thread started")
    
    def stop_background_refresh(self):
        """Stop the background refresh thread"""
        self._stop_refresh.set()
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1)
            self.refresh_thread = None
    
    def _background_refresh_loop(self):
        """Background thread loop for refreshing mesh data"""
        while not self._stop_refresh.is_set():
            try:
                if self._stop_refresh.wait(REFRESH_INTERVAL_SECONDS):
                    break  # Stop event was set
                logging.info("Background refresh: Reading mesh data...")
                self.data_service.read_mesh_data()
            except Exception as e:
                logging.error(f"Error in background refresh: {e}")
    
    def monitor_data_updates_blocking(self):
        """Blocking method to monitor data updates (for standalone use)"""
        self.start_file_monitor()
        try:
            while True:
                time.sleep(REFRESH_INTERVAL_SECONDS)
                logging.info("Checking for mesh data updates.")
                self.data_service.read_mesh_data()
        except KeyboardInterrupt:
            logging.info("Stopping file monitor...")
        finally:
            self.stop_file_monitor()


# This will be initialized by the main application
file_monitor_service = None
