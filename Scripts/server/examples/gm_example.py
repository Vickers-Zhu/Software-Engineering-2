"""
Game Master example
Creates a new game then adds `"result": "OK"` to all received JSONs

based on https://twistedmatrix.com/documents/current/_downloads/echoclient.py
"""

from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
import json


class PlayerExample(LineReceiver):
    """
    The only class we care about
    """

    # either write strings this way or use strings' .encode() method
    message_start = b'{ "action": "start" }'

    def connectionMade(self):
        print("\n", "send:", self.message_start, "\n")  # prints the sent line
        self.transport.write(self.message_start)  # send `message_connect` to the server

    def lineReceived(self, line):
        print("\n", "receive:", line, "\n")  # prints received line
        parsed_json = json.loads(line)  # now the whole JSON is in this variable as a dictionary

        # if it's a game start message
        if "action" in parsed_json and parsed_json["action"] == "start":
            # check if the result is equal OK in the received JSON
            if "result" in parsed_json and not parsed_json["result"] == "OK":
                print("fail")
                self.transport.loseConnection()  # cleanly closes the connection
        else:
            # add result OK to all other types of messages
            parsed_json["result"] = "OK"
            result = json.dumps(parsed_json).encode()
            print("\n", "send:", result, "\n")  # prints the sent line
            self.transport.write(result)

    def rawDataReceived(self, data):  # not important, just needs to be implemented
        pass


class EchoClientFactory(ClientFactory):  # no need to change anything there
    protocol = PlayerExample

    def __init__(self):
        self.done = Deferred()

    def clientConnectionFailed(self, connector, reason):
        print('connection failed:', reason.getErrorMessage())
        self.done.errback(reason)

    def clientConnectionLost(self, connector, reason):
        print('connection lost:', reason.getErrorMessage())
        self.done.callback(None)


def main(reactor):
    factory = EchoClientFactory()
    reactor.connectTCP('localhost', 9998, factory)
    return factory.done


if __name__ == '__main__':
    task.react(main)
