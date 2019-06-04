Responsibility of Igor Sałuch

# The Project Game Server

## Usage 
Run `python3 server.py --port=<port>`, where `<port>` is a chosen port on which the server should be started.

For example, 

`python3 server.py --port=2137`

or just

`./server.py -p 2137`

## Technical details
* uses TCP sockets
* passes JSON messages separated by a bytecode 23 (ETB)
* Uses ETB also as keep-alive data
* everything in text mode
* serve at least 16 players
* ability to serve one game a time
* ability to set interval between keep alive bytes (or expected keep alive) 
