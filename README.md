# Meshtastic Mesh Visualizer

This repository contains the code for the Meshtastic Mesh Visualizer. The following instructions will guide you on how to build and deploy the Docker image using the provided script.

## Prerequisites

- Docker
- Docker Compose
- Git

## Usage

The `build_and_deploy_image.sh` script automates the process of building and deploying the Docker image. Follow the steps below to use the script:

1. Clone the repository:
    ```bash
    git clone https://github.com/yourusername/meshtastic_mesh_visualizer.git
    cd meshtastic_mesh_visualizer
    ```

2. Make the script executable:
    ```bash
    chmod +x build_and_deploy_image.sh
    ```

3. Run the script with the desired branch name (defaults to `main` if no branch is specified):
    ```bash
    ./build_and_deploy_image.sh [branch_name]
    ```

    For example, to deploy the `develop` branch:
    ```bash
    ./build_and_deploy_image.sh develop
    ```

## Script Details

The script performs the following steps:

1. Checks out to the specified branch.
2. Pulls the latest changes from the repository.
3. Stops and removes any existing Docker containers for the image.
4. Builds the Docker image.
5. Runs Docker Compose in detached mode.
6. Follows the Docker logs.

## Integration with Mesh Monitor

The `mesh_visualizer` works in conjunction with the `mesh_monitor` to provide real-time visualization of the mesh network. The `mesh_monitor` collects data from the mesh network and sends it to the `mesh_visualizer` for display.

To set up the integration:

1. Ensure that the `mesh_monitor` is running and collecting data from the mesh network.
2. Configure the `mesh_visualizer` to receive data from the `mesh_monitor`. This can typically be done by setting environment variables or configuration files (refer to the specific configuration details in the `mesh_visualizer` documentation).
3. Start the `mesh_visualizer` using the provided script or Docker Compose.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
