# A Powershell Script that starts the manylinux docker, mounts the script and wheel directories

$script_dir = Resolve-Path -Path "."

if (-not (Test-Path ./wheels)) {
    mkdir ./wheels
}
$wheel_dir = Resolve-Path -Path "./wheels"

docker run -it `
       --mount type=bind,src=$script_dir,destination=/scripts `
       --mount type=bind,src=$wheel_dir,destination=/wheels `
       quay.io/pypa/manylinux2010_x86_64 `
       /bin/bash
