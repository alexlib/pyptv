# PyPTV Docker Setup

This is a simple Docker setup for running PyPTV with a graphical interface accessible through your web browser.

## Quick Start

### On Linux/macOS:

```bash
./docker-pyptv.sh
```

### On Windows:

```
docker-pyptv.bat
```

That's it! The script will:
1. Create a Docker container with all necessary dependencies
2. Install PyPTV inside the container
3. Set up noVNC for web-based access
4. Open your browser to http://localhost:6901/vnc.html?password=

## Accessing PyPTV

Once the desktop loads in your browser:
- Double-click the PyPTV icon on the desktop, or
- Open a terminal and run: `/headless/start_pyptv.sh`

## Working with Files

The `data` directory on your host system is mounted to `/headless/work` inside the container. This means:

- Files you create in the `/headless/work` directory inside the container will appear in the `data` directory on your host system
- Files you place in the `data` directory on your host system will be accessible at `/headless/work` inside the container

## Stopping the Container

To stop the container:

```bash
docker stop pyptv-container
```

To remove the container:

```bash
docker rm pyptv-container
```

## Troubleshooting

If you encounter issues:

1. Check the container logs:
   ```bash
   docker logs pyptv-container
   ```

2. Make sure ports 6901 is not being used by another application

3. If the container fails to start, try increasing the shared memory size in the script (--shm-size=2g)
