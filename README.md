# chat.dataweek.de

The chat middle ware. It provides a socket.io interface to relay the messages from and to the matrix room. A simple chat interface is part of this repo, is available at [AKSW/lswt2021.stream](https://github.com/AKSW/lswt2021.stream), and is part of the dataweek page at [AKSW/leipzig.dataweek.de](https://github.com/AKSW/leipzig.dataweek.de).


## Development Requirements
- Taskfile
- Poetry
- Python

## Execution Requirements
- podman/docker
- podman-compose/docker-compose

## Some notes for the Matrix nio dependency:

Check out: https://github.com/poljar/matrix-nio#installation.
It also requires the pacakges: `libolm-dev` resp. `libolm-devel`.
