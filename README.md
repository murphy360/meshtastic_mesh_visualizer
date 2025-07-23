# Meshtastic Mesh Visualizer

A Flask-based web application for visualizing Meshtastic mesh networks with real-time updates and interactive maps.

## Table of Contents
- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Automated Setup](#automated-setup)
- [Manual Setup](#manual-setup)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Development](#development)
- [Docker Deployment](#docker-deployment)
- [Contributing](#contributing)

## Quick Start

The fastest way to get started is using our automated setup scripts. Choose your platform:

### Windows Users
```cmd
# Option 1: Simple batch file (recommended for beginners)
setup_and_test.bat

# Option 2: PowerShell script (more features)
scripts\setup_and_test.ps1

# Option 3: Cross-platform Python script
python setup_and_test.py
```

### Linux/Mac Users
```bash
# Option 1: Shell script
chmod +x setup_and_test.sh
./setup_and_test.sh

# Option 2: Cross-platform Python script
python3 setup_and_test.py
```

## Prerequisites

- **Python 3.8+** (required for all setups)
- **Git** (for cloning the repository)
- **Docker & Docker Compose** (optional, for containerized deployment)

## Automated Setup

All setup scripts provide identical functionality across platforms and handle:

1. **Python Detection**: Find and validate a working Python interpreter
2. **Virtual Environment**: Automatically create and manage `.venv/`
3. **Dependencies**: Install all required packages from `requirements.txt`
4. **Test Dependencies**: Install pytest, coverage, and testing tools
5. **Project Validation**: Verify required files and directory structure
6. **Test Data**: Configure test datasets for development
7. **Testing**: Run comprehensive test suite to verify setup
8. **Application Validation**: Test Flask app startup

### Setup Script Options

All scripts support these command-line options:

- `--setup-only` / `-SetupOnly`: Only run setup, skip tests
- `--test-only` / `-TestOnly`: Only run tests (assumes setup is done)
- `--clean` / `-Clean`: Clean install (remove existing `.venv`)
- `--no-tests` / `-NoTests`: Skip all tests
- `--help` / `-Help`: Show help message

### Examples

```bash
# Full setup and testing (default)
./setup_and_test.sh

# Clean install without tests
./setup_and_test.sh --clean --no-tests

# Setup only for development
python setup_and_test.py --setup-only

# Run tests only (after setup)
scripts\setup_and_test.ps1 -TestOnly
```

## Manual Setup

If you prefer manual setup or the automated scripts don't work for your environment:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/murphy360/meshtastic_mesh_visualizer.git
   cd meshtastic_mesh_visualizer
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv .venv
   
   # Activate on Windows
   .venv\Scripts\activate
   
   # Activate on Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install pytest pytest-cov pytest-html
   ```

4. **Configure test data**:
   ```bash
   python scripts/test_data_switcher.py small
   ```

## Usage

### Running the Application

After setup, you can run the mesh visualizer:

```bash
# Using the virtual environment Python directly
.venv/Scripts/python src/app.py  # Windows
.venv/bin/python src/app.py      # Linux/Mac

# Or activate the virtual environment first
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate          # Windows
python src/app.py
```

The application will start on `http://127.0.0.1:5000` with real-time mesh network visualization.

### Application Features

- **Interactive Map**: Folium-based interactive mesh network visualization
- **Real-time Updates**: Background file monitoring for live data updates
- **Node Management**: Display mesh nodes with position, status, and metadata
- **Filtering**: Show/hide nodes based on various criteria
- **Coverage Visualization**: Display mesh coverage areas and hop distances
- **SITREP Display**: Network status summary and statistics

### Test Data Management

Switch between different test datasets:

```bash
# List available datasets
python scripts/test_data_switcher.py list

# Switch to different datasets
python scripts/test_data_switcher.py small    # Small test dataset
python scripts/test_data_switcher.py large    # Large test dataset  
python scripts/test_data_switcher.py minimal  # Minimal test dataset
```

## Project Structure

```
meshtastic_mesh_visualizer/
├── src/                          # Application source code
│   ├── app.py                   # Main Flask application
│   ├── config/                  # Configuration management
│   │   ├── settings.py          # App settings and defaults
│   │   └── colors.py            # Color schemes for visualization
│   ├── models/                  # Data models
│   │   ├── mesh_data.py         # Mesh network data model
│   │   └── node.py              # Individual node model
│   ├── services/                # Business logic services
│   │   ├── data_service.py      # Data loading and management
│   │   ├── map_service.py       # Map generation and rendering
│   │   ├── file_monitor.py      # Real-time file monitoring
│   │   └── polygon_service.py   # Geographic polygon operations
│   ├── utils/                   # Utility functions
│   │   ├── time_utils.py        # Time and date utilities
│   │   ├── geo_utils.py         # Geographic calculations
│   │   └── template_utils.py    # HTML template utilities
│   ├── templates/               # Jinja2 HTML templates
│   └── static/                  # Static web assets (CSS, JS, images)
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   │   ├── test_node.py         # Node model tests
│   │   ├── test_mesh_data.py    # Mesh data tests
│   │   └── test_data_service.py # Data service tests
│   ├── integration/             # Integration tests
│   │   └── test_workflow.py     # End-to-end workflow tests
│   ├── data/                    # Test datasets
│   │   ├── mesh_data.json       # Active test data (symlink)
│   │   ├── mesh_data_small.json # Small dataset
│   │   ├── mesh_data_large.json # Large dataset
│   │   └── mesh_data_minimal.json # Minimal dataset
│   ├── conftest.py              # Pytest configuration and fixtures
│   └── run_tests.py             # Unified test runner
├── scripts/                     # Automation and utility scripts
│   ├── setup_and_test.ps1       # PowerShell setup script
│   ├── test_app_simple.ps1      # Simple PowerShell test runner
│   ├── test_app.bat             # Batch file test runner
│   ├── test_runner.py           # Python test automation
│   └── test_data_switcher.py    # Test data management
├── setup_and_test.py            # Main cross-platform automation
├── setup_and_test.bat           # Windows batch automation
├── setup_and_test.sh            # Unix shell automation
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Docker container definition
├── docker-compose.yaml          # Docker Compose configuration
└── README.md                    # This file
```

## Testing

### Running Tests

The project includes comprehensive unit and integration tests:

```bash
# Run all tests
python -m pytest tests/ -v

# Run only unit tests
python -m pytest tests/unit/ -v

# Run only integration tests
python -m pytest tests/integration/ -v

# Run tests with coverage report
python -m pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
python -m pytest tests/unit/test_node.py -v
```

### Test Scripts

Use the provided test automation scripts:

```bash
# PowerShell (Windows) - Most feature-rich
scripts\test_app_simple.ps1 [-TestData <dataset>] [-Clean] [-Setup]

# Batch file (Windows) - Simple
scripts\test_app.bat

# Python script (Cross-platform)
python scripts/test_runner.py --test-data small --clean
```

### Test Data

The project includes multiple test datasets:

- **Small**: Quick testing with minimal nodes
- **Large**: Comprehensive testing with many nodes
- **Minimal**: Basic functionality testing

Use `scripts/test_data_switcher.py` to switch between datasets.

## Development

### Development Workflow

1. **Setup**: Use automated setup scripts for initial environment
2. **Development**: Make changes to source code in `src/`
3. **Testing**: Run tests frequently during development
4. **Data**: Use test data switcher to test with different datasets
5. **Validation**: Run integration tests before committing

### Key Services

- **DataService**: Handles loading and caching of mesh data
- **MapService**: Generates interactive Folium maps
- **FileMonitorService**: Provides real-time updates when data changes
- **PolygonService**: Handles geographic calculations and coverage areas

### Configuration

Main configuration in `src/config/settings.py`:
- Default visibility settings
- Map configuration
- File paths and monitoring settings
- Application defaults

### Adding Features

1. **Models**: Add new data models in `src/models/`
2. **Services**: Implement business logic in `src/services/`
3. **Views**: Add Flask routes in `src/app.py`
4. **Tests**: Add corresponding tests in `tests/unit/` or `tests/integration/`
5. **Documentation**: Update this README and add inline documentation

## Docker Deployment

### Build and Deploy Script

The `build_and_deploy_image.sh` script automates Docker deployment:

```bash
# Make script executable
chmod +x build_and_deploy_image.sh

# Deploy main branch (default)
./build_and_deploy_image.sh

# Deploy specific branch
./build_and_deploy_image.sh develop
```

### Manual Docker Commands

```bash
# Build the image
docker build -t meshtastic_mesh_visualizer .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Integration with Mesh Monitor

The mesh visualizer works with the `mesh_monitor` component:
1. `mesh_monitor` collects data from Meshtastic devices
2. Data is written to JSON files
3. `mesh_visualizer` monitors files and updates the visualization
4. Real-time updates provide live network status

## Contributing

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Use automated setup: `./setup_and_test.sh` or `setup_and_test.bat`
4. Make your changes
5. Run tests: `python -m pytest tests/ -v`
6. Commit your changes: `git commit -am 'Add some feature'`
7. Push to the branch: `git push origin feature/your-feature-name`
8. Submit a pull request

### Code Standards

- Follow PEP 8 Python style guidelines
- Add type hints for new functions
- Include docstrings for new classes and methods
- Add tests for new functionality
- Update documentation as needed

### Testing Requirements

- All new features must include tests
- Maintain or improve test coverage
- Run the full test suite before submitting PRs
- Use the test data switcher to test with different datasets

### Architecture Notes

The application follows a clean architecture pattern:
- **Models**: Pure data models with minimal logic
- **Services**: Business logic and external integrations
- **Controllers**: Flask routes and request handling
- **Utils**: Pure functions for common operations
- **Config**: Centralized configuration management

This structure promotes maintainability, testability, and clear separation of concerns.

---

For detailed information about specific components, refer to the inline documentation in the source code. For issues or questions, please open a GitHub issue.
