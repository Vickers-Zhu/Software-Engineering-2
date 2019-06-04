"""
Player example
Joins an existing game

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

    message_connect = \
        b'{ "action": "connect", "preferredTeam": "blue", "type": "player", "userGuid": "123hoj2" }'

    def connectionMade(self):
        print("\n", "send:", self.message_connect, "\n")  # prints the sent line
        self.transport.write(self.message_connect)  # send `message_connect` to the server

    def lineReceived(self, line):
        print("\n", "receive:", line, "\n")  # prints received line
        parsed_json = json.loads(line)  # now the whole JSON is in this variable as a dictionary

        # check if the result is equal OK in the received JSON
        if "result" in parsed_json and parsed_json["result"] == "OK":
            print("success")
            self.transport.loseConnection()  # cleanly closes the connection

    def rawDataReceived(self, data):
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
