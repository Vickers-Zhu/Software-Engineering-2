#!/usr/bin/env python3

import getopt
import json
import sys

from twisted.internet import reactor, protocol

from player import Player


class GameProtocol(protocol.Protocol):
    delimiter = b'\x17'

    def connectionMade(self):
        print("Connected", self)
        self.factory.clients.append(self)

    def connectionLost(self, reason):
        print("Disconnected from", self, reason.value)
        self.factory.clients.remove(self)

    def dataReceived(self, data):
        print("received", repr(data))
        if data == GameProtocol.delimiter:
            # for easier debugging
            return
        if data == b'gui':
            self.factory.gui = self
            return
        for d in data.split(GameProtocol.delimiter):
            if d != b'':
                self.handle(self, d)

    def message(self, message):
        self.transport.write(message + GameProtocol.delimiter)

    def handle(self, addr, data):
        # print("received data:", addr, data)
        parsed_json = json.loads(data)
        if "action" not in parsed_json:
            print("ERROR: NO ACTION FIELD IN THE MESSAGE")
            return
        action = parsed_json["action"]
        print("action:", action)

        if action == 'gui':
            self.factory.gui.message(data)
            return
        if action == "start":
            if not hasattr(self.factory, 'game_master'):
                print("RegisterGame", addr)
                self.factory.game_master = self
                parsed_json["result"] = "OK"
                self.message(json.dumps(parsed_json).encode())
            else:
                if "teamGuids" not in parsed_json:
                    print("ERROR: GAME ALREADY REGISTERED")
                    parsed_json["result"] = "denied"
                    self.message(json.dumps(parsed_json).encode())
                    return
                print("BeginGame")
                # Note: no need to send to players in teamGuids, gm sends message for each one either way
                gid = parsed_json['userGuid']
                self.factory.players[gid].address.message(data)

        elif action == "connect":
            print("JoinGame", addr)
            if "userGuid" not in parsed_json:
                print("ERROR: NO GUID GIVEN")
                return
            guid = parsed_json["userGuid"]

            if "result" not in parsed_json:
                self.factory.game_master.message(data)
                self.factory.waitroom[guid] = Player(addr, guid)

            if "result" in parsed_json:
                if parsed_json["result"] == "OK":
                    self.factory.players[guid] = (self.factory.waitroom.pop(guid))
                    self.factory.players[guid].address.message(data)

                if parsed_json["result"] == "denied":
                    self.factory.waitroom[guid].address.message(data)
                    self.factory.waitroom[guid].address.transport.loseConnection()
                    self.factory.waitroom.pop(guid)

        elif action == "end":
            print("GameOver", addr)
            # send message to all players
            for guid in self.factory.players:
                self.factory.players[guid].address.message(data)

        elif action == "exchange":
            if "receiverGuid" in parsed_json:
                print("AuthorizeKnowledgeExchange", addr)
                if addr != self.factory.game_master:
                    self.factory.game_master.message(data)
                else:
                    receiver_guid = parsed_json["receiverGuid"]
                    self.factory.players[receiver_guid].address.message(data)
            elif "result" and "userGuid" in parsed_json:
                print("{Accept,Reject}KnowledgeExchange", addr)
                if addr != self.factory.game_master:
                    self.factory.game_master.message(data)
                else:
                    guid = parsed_json["userGuid"]
                    self.factory.players[guid].address.message(data)

        elif action == "send":
            if "receiverGuid" in parsed_json:
                if addr != self.factory.game_master:
                    self.factory.game_master.message(data)
                else:
                    print("Data", addr)
                    receiver_guid = parsed_json["receiverGuid"]
                    self.factory.players[receiver_guid].address.message(data)

        else:
            # all other gameplay messages
            if "userGuid" in parsed_json:
                if "result" in parsed_json:
                    guid = parsed_json["userGuid"]
                    self.factory.players[guid].address.message(data)
                else:
                    self.factory.game_master.message(data)


if __name__ == '__main__':

    def usage():
        print("usage:", sys.argv[0], "[--port=<port> | -p <port>]")

    port = -1

    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "hp:", ["help", "port="])
        for opt, value in opts:
            if opt in ("-h", "--help"):
                usage()
                sys.exit()
            elif opt in ("-p", "--port"):
                if str.isdigit(value):
                    port = int(value)
                else:
                    print("ERROR: Given port number is not a digit")
                    usage()
                    sys.exit(2)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    if port == -1:
        usage()
        sys.exit(2)

    factory = protocol.ServerFactory()
    factory.protocol = GameProtocol
    factory.clients = []
    factory.waitroom = {}
    factory.players = {}
    print("Server starting on port", port)
    reactor.listenTCP(port, factory)
    reactor.run()
