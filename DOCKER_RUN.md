# Running PyPTV with Docker

This guide provides step-by-step instructions for running PyPTV using Docker with a graphical interface accessible through your web browser. This approach works on any platform that supports Docker (Windows, macOS, Linux).

> **Note**: We provide two different Docker setups:
> 1. **Kasm Setup** (Recommended): Uses the kasmweb base image which provides a more reliable VNC experience
> 2. **Standard Setup**: Uses a custom-built VNC setup

## Kasm Setup (Recommended)

### Quick Start

1. **Create a data directory**
   ```bash
   mkdir -p data
   ```

2. **Start the container**
   ```bash
   # On Linux/macOS:
   ./run_kasm_docker.sh

   # On Windows:
   run_kasm_docker.bat
   ```

3. **Access PyPTV**
   - Open your web browser and go to: http://localhost:6901
   - You'll be connected automatically without a password
   - Start PyPTV using the desktop shortcut or by running `/home/kasm-default-profile/start_pyptv.sh` in a terminal

That's it! You're now running PyPTV in a Docker container with full GUI access.

## Standard Setup

### Running PyPTV in 3 Simple Steps

1. **Create a data directory**
   ```bash
   mkdir -p data
   ```

2. **Start the container**
   ```bash
   # On Linux/macOS:
   ./run_pyptv_docker.sh

   # On Windows:
   run_pyptv_docker.bat
   ```

3. **Access PyPTV**
   - Open your web browser and go to: http://localhost:6080/vnc.html
   - You'll be connected automatically without a password
   - Start PyPTV using the desktop shortcut or by running `/home/pyptv/start_pyptv.sh` in a terminal

That's it! You're now running PyPTV in a Docker container with full GUI access.

## Detailed Instructions

### Setting Up Docker

#### Windows
1. Install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
2. Make sure WSL 2 is enabled (Docker Desktop will guide you)
3. Start Docker Desktop and wait for it to be running (check the system tray icon)

#### macOS
1. Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
2. Start Docker Desktop and wait for it to be running (check the menu bar icon)

#### Linux
1. Install Docker using your distribution's package manager:
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install docker.io docker-compose

   # Fedora
   sudo dnf install docker docker-compose

   # Arch Linux
   sudo pacman -S docker docker-compose
   ```
2. Start and enable the Docker service:
   ```bash
   sudo systemctl start docker
   sudo systemctl enable docker
   ```
3. Add your user to the docker group to run Docker without sudo:
   ```bash
   sudo usermod -aG docker $USER
   ```
   (Log out and back in for this to take effect)

### Running PyPTV for the First Time

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/alexlib/pyptv.git
   cd pyptv
   ```

2. **Create a data directory** for your PyPTV projects:
   ```bash
   mkdir -p data
   ```

3. **Build and start the container**:
   ```bash
   # Using docker-compose directly
   docker-compose up -d

   # Or using the provided scripts
   ./run_pyptv_docker.sh  # Linux/macOS
   run_pyptv_docker.bat   # Windows
   ```
   The first time you run this, it will build the Docker image, which may take several minutes.

4. **Access the PyPTV GUI**:
   - Open your web browser and navigate to: http://localhost:6080/vnc.html
   - You'll be connected automatically without a password
   - You'll see a Linux desktop environment running inside your browser

5. **Start PyPTV**:
   - Double-click the PyPTV desktop shortcut, or
   - Open a terminal and run: `/home/pyptv/start_pyptv.sh`

### Working with Files

The `data` directory on your host system is mounted to `/home/pyptv/work` inside the container. This means:

- Files you create in the `/home/pyptv/work` directory inside the container will appear in the `data` directory on your host system
- Files you place in the `data` directory on your host system will be accessible at `/home/pyptv/work` inside the container

This allows you to:
1. Prepare your data on your host system using familiar tools
2. Process the data using PyPTV in the container
3. Access the results on your host system without copying files

### Stopping and Restarting

- **To stop the container**:
  ```bash
  docker-compose down
  ```

- **To restart the container**:
  ```bash
  docker-compose up -d
  ```

- **To restart and rebuild the container** (if you've made changes to the Dockerfile):
  ```bash
  docker-compose up -d --build
  ```

## Advanced Usage

### Customizing the Setup

#### Changing the Screen Resolution

Edit the `docker-compose.yml` file and modify the `RESOLUTION` environment variable:

```yaml
environment:
  - RESOLUTION=1280x720  # Change to your preferred resolution
```

Common resolutions:
- 1280x720 (720p)
- 1920x1080 (1080p)
- 2560x1440 (1440p)

#### Changing the Data Directory

Edit the `docker-compose.yml` file and modify the volume mount:

```yaml
volumes:
  - /path/to/your/data:/home/pyptv/work  # Change to your preferred path
```

#### Using a Different Port

If port 6080 is already in use on your system, you can change it in the `docker-compose.yml` file:

```yaml
ports:
  - "8080:6080"  # Change 8080 to your preferred port
```

Then access noVNC at http://localhost:8080/vnc.html

### Direct VNC Connection

If you prefer to use a VNC client instead of the web interface:

1. Connect to `localhost:5900` using your VNC client
2. No password is required

This can provide better performance than the web interface.

### Running Commands in the Container

To run commands inside the container:

```bash
# Get the container name
docker ps

# Run a command (replace pyptv_pyptv_1 with your container name)
docker exec -it pyptv_pyptv_1 bash
```

This gives you a shell inside the container where you can run commands.

## Troubleshooting

### If You're Having Connection Issues

If you're experiencing connection issues with the standard setup, we recommend trying the Kasm setup instead:

```bash
# On Linux/macOS:
./run_kasm_docker.sh

# On Windows:
run_kasm_docker.bat
```

The Kasm setup uses a more reliable base image (kasmweb) that has better compatibility across different systems.

### Container Not Starting

Check the logs for error messages:

```bash
docker-compose logs
```

Common issues:
- Port conflicts: Change the port in docker-compose.yml
- Insufficient permissions: Make sure you have permission to use Docker
- Insufficient resources: Allocate more CPU/memory to Docker in Docker Desktop settings

### Cannot Access noVNC

If you can't access the noVNC interface:

1. Check if the container is running:
   ```bash
   docker ps
   ```

2. Check if the ports are correctly mapped:
   ```bash
   docker-compose ps
   ```

3. Try accessing with a different browser or in incognito mode

4. Check if a firewall is blocking the connection

### PyPTV Not Starting

If PyPTV doesn't start inside the container:

1. Check if all dependencies are installed:
   ```bash
   docker exec -it pyptv_pyptv_1 pip list
   ```

2. Try running PyPTV manually in a terminal inside the container:
   ```bash
   cd /home/pyptv/work
   python3 -m pyptv.pyptv_gui
   ```

3. Check for error messages in the terminal output

### Performance Issues

If the GUI feels slow or unresponsive:

1. Try reducing the screen resolution in docker-compose.yml
2. Allocate more resources to Docker (in Docker Desktop settings)
3. Use a direct VNC connection instead of the web interface
4. Close other resource-intensive applications

### File Permission Issues

If you encounter permission issues with files:

1. The container runs as a non-root user (pyptv)
2. You may need to adjust permissions on your host files:
   ```bash
   chmod -R 755 data
   ```

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [PyPTV GitHub repository](https://github.com/alexlib/pyptv) for updates
2. Open an issue on GitHub with details about your problem
3. Join the PyPTV community discussions

## License

PyPTV is licensed under the terms of the GNU General Public License v3.0.
