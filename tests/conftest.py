"""
Test configuration and fixtures for Meshtastic Mesh Visualizer
"""
import pytest
import sys
import os
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Test data paths
TEST_DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture
def test_data_dir():
    """Fixture providing path to test data directory"""
    return TEST_DATA_DIR


@pytest.fixture
def sample_mesh_data():
    """Fixture providing sample mesh data for testing"""
    return {
        "last_update": "2025-07-23T14:30:00Z",
        "sitrep_time": "2025-07-23T14:30:00Z",
        "nodes": [
            {
                "id": "TEST_PRIMARY",
                "lat": 37.7749,
                "lon": -122.4194,
                "alt": 150,
                "lastHeard": "",
                "hopsAway": 0,
                "connections": ["TEST_SECONDARY"],
                "precision_bits": 32
            },
            {
                "id": "TEST_SECONDARY",
                "lat": 37.8044,
                "lon": -122.2711,
                "alt": 200,
                "lastHeard": "1721741700",
                "hopsAway": 0,
                "connections": ["TEST_PRIMARY"],
                "precision_bits": 16
            }
        ],
        "sitrep": [
            "Test SITREP line 1",
            "Test SITREP line 2"
        ]
    }


@pytest.fixture
def sample_node_data():
    """Fixture providing sample node data for testing"""
    return {
        "id": "TEST_NODE",
        "lat": 37.7749,
        "lon": -122.4194,
        "alt": 150,
        "lastHeard": "1721741700",
        "hopsAway": 1,
        "connections": ["PRIMARY_NODE"],
        "precision_bits": 16
    }


@pytest.fixture
def visibility_settings():
    """Fixture providing default visibility settings"""
    return {
        'show_last_hour': True,
        'show_last_day': True,
        'show_last_week': True,
        'show_over_week': True,
        'show_no_last_heard': False,
        'show_receive_range': False,
        'show_receive_range_1hop': False,
        'show_receive_range_2hop': False,
        'show_receive_range_3hop': False
    }
