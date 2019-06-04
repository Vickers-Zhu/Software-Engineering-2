Responsibility of Marin Karamihalev

Please make sure you have installed these packages first:
    > pip install multipledispatch
    > pip install pypubsub

Usage:
    Import external.py, messages.py and uuid (built-in library) to your code. Initialize GmExternal, with a server callback function as the argument. 
    To send messages use send_message function with a message class from the message.py file.
    
    Example:

        import external as ext
        import messages as m
        import uuid

        # Required structure of the server callback function.
        # All messages meant for the server will pass through this function
        def server_callback(arg1):
            print("got a message from the gm")

        # Initialize game master
        gm = ext.GmExternal(server_callback)

        # Example of joining a game
        player_id = uuid.uuid4()
        msg = m.JoinGame(preferred_team='blue', type='player', id=player_id)

        # Sending message to game master, response will be passed to the server_callback function
        gm.send_message(msg)

