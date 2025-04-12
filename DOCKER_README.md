# PyPTV with noVNC Docker Setup

This Docker setup allows you to run PyPTV with a graphical interface accessible through your web browser. It works on any platform that supports Docker (Windows, macOS, Linux) without requiring platform-specific dependencies.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (included with Docker Desktop for Windows and macOS)

## Quick Start

1. Create a data directory for your PyPTV projects:

```bash
mkdir -p data
```

2. Build and start the Docker container:

```bash
docker-compose up -d
```

3. Access the PyPTV GUI by opening your web browser and navigating to:

```
http://localhost:6080/vnc.html
```

4. When prompted for a password, enter: `pyptv`

5. Once connected, you can start PyPTV by double-clicking the PyPTV desktop shortcut or by opening a terminal and running:

```bash
/home/pyptv/start_pyptv.sh
```

## File Access

The `data` directory on your host system is mounted to `/home/pyptv/work` inside the container. Any files you save in this directory from within the container will be accessible on your host system, and vice versa.

## Customization

### Screen Resolution

You can change the screen resolution by modifying the `RESOLUTION` environment variable in the `docker-compose.yml` file:

```yaml
environment:
  - RESOLUTION=1920x1080  # Change to your preferred resolution
```

Common resolutions:
- 1280x720 (720p)
- 1920x1080 (1080p)
- 2560x1440 (1440p)

### Data Directory

You can change the location of the data directory by modifying the volume mount in the `docker-compose.yml` file:

```yaml
volumes:
  - /path/to/your/data:/home/pyptv/work  # Change to your preferred path
```

## Advanced Usage

### Direct VNC Connection

If you prefer to use a VNC client instead of the web interface, you can connect to `localhost:5901` using the password `pyptv`.

### Running Commands

To run commands inside the container:

```bash
docker exec -it pyptv_pyptv_1 bash
```

### Stopping the Container

To stop the container:

```bash
docker-compose down
```

## Troubleshooting

### Connection Issues

If you cannot connect to the noVNC interface, check that:

1. The container is running: `docker ps`
2. The ports are correctly mapped: `docker-compose ps`
3. There are no firewall issues blocking the ports

### Performance Issues

If the GUI feels slow or unresponsive:

1. Try reducing the screen resolution
2. Allocate more resources to Docker (in Docker Desktop settings)
3. Use a direct VNC connection instead of the web interface

### File Permission Issues

If you encounter permission issues with files:

1. The container runs as a non-root user (pyptv)
2. You may need to adjust permissions on your host files: `chmod -R 777 data`

## Building from Source

If you want to build the Docker image from the source code:

1. Clone the repository:

```bash
git clone https://github.com/alexlib/pyptv.git
cd pyptv
```

2. Build and run the container:

```bash
docker-compose up -d --build
```

## License

PyPTV is licensed under the terms of the GNU General Public License v3.0.
