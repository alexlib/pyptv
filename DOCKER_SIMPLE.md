# PyPTV Simple Docker Setup

This is a simplified Docker setup for running PyPTV with a graphical interface accessible through your web browser.

## Quick Start

### On Linux/macOS:

```bash
./run_pyptv_simple.sh
```

### On Windows:

```
run_pyptv_simple.bat
```

That's it! The script will:
1. Pull the dorowu/ubuntu-desktop-lxde-vnc image (a reliable base image with noVNC)
2. Start a container with the image
3. Install all necessary dependencies inside the container
4. Install PyPTV inside the container
5. Create a desktop shortcut for PyPTV
6. Open your browser to http://localhost:6080

## Accessing PyPTV

Once the desktop loads in your browser:
- Double-click the PyPTV icon on the desktop, or
- Open a terminal and run: `/home/ubuntu/start_pyptv.sh`

## Working with Files

The `data` directory on your host system is mounted to `/home/ubuntu/work` inside the container. This means:

- Files you create in the `/home/ubuntu/work` directory inside the container will appear in the `data` directory on your host system
- Files you place in the `data` directory on your host system will be accessible at `/home/ubuntu/work` inside the container

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

2. Make sure port 6080 is not being used by another application

3. If the container fails to start, try increasing the shared memory size in the script (--shm-size=2g)
