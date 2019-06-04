# Files
- `gm_example.py` - Game Master example

Creates a new game then adds `"response": "OK"` to all received JSONs

- `player_example.py` - Player example

Joins an existing game

Both programs are simple TCP clients using Twisted library, connecting to 
the server on default port and address and communicating via JSON-formatted messages,
as described in the project documentation.

Both programs print all received messages.

# Usage 
Assuming working in the root of the repository and with server requirements installed:

1. Run the server:
`python3 Scripts/server/server.py`

2. Run the game master example:
`python3 Scripts/server/examples/gm_example.py`

3. Run the player example:
`python3 Scripts/server/examples/gm_example.py`
