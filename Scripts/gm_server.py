from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
import argparse
import asyncio

import external as ext
import common.messages as m


class GM_Server(LineReceiver):

    def __init__(self):
        self.gm = None
        self.gui = EchoClientFactory.gui
        self.delimiter = b'\x17'

    def write_msg(self, msg: m.Message):
        line = msg.to_json().encode() + self.delimiter
        print(f"> gm server: Sending \"{line}\"")
        self.transport.write(line)

    def write_msg_no_print(self, msg: m.Message):
        line = msg.to_json().encode() + self.delimiter
        self.transport.write(line)

    def pass_to_server(self, arg1):
        self.write_msg(arg1)

    def pass_to_gui(self, arg1):
        msg = m.GuiMessage(arg1)
        self.write_msg_no_print(msg)

    # Ignore gui messages, if the gui flag was not set
    def ignore_gui(self, arg1):
        pass

    def connectionMade(self):
        # Send game start message to server
        self.write_msg(m.SetUpGame())

    def game_over(self):
        print('> gm server: Game over, shutting down')
        self.transport.loseConnection()

    def lineReceived(self, line):
        print(f"> gm server: Got \"{line}\"")
        # Translate json to msg
        msg, err = m.Message.from_json_gm(line)

        # If the message could not be translated
        if err is not None:
            print(f'> gm server: Could not translate line \n \"{err}\"')
            return

        # If it's a game start message
        if type(msg) is m.ConfirmSetUpGame:
            # If game is not accepted
            if msg.result == 'denied':
                print('> gm server: Could not start game')
                self.transport.loseConnection()
                self.gm = None
                return
            # If new game is accepted
            else:
                # Start game
                print('> gm server: Started new game')
                self.gm = ext.GmExternal(
                    self.pass_to_server, self.pass_to_gui if self.gui else self.ignore_gui)

        # For general game messages
        else:
            # Send to gm to deal with it
            self.gm.send_message(msg)
            return

    def rawDataReceived(self, data):  # not important, just needs to be implemented
        pass


# Default (almost) client factory from the twisted python documentation
class EchoClientFactory(ClientFactory):
    gui = False

    def __init__(self, gui=False):
        self.done = Deferred()
        EchoClientFactory.gui = gui
        EchoClientFactory.protocol = GM_Server

    def clientConnectionFailed(self, connector, reason):
        self.done.errback(reason)

    def clientConnectionLost(self, connector, reason):
        self.done.callback(None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-a', '--address', help='IPv4/v6 address or host name', default='localhost')
    parser.add_argument(
        '-p', '--port', help='Server port number', type=int, default=9997)
    parser.add_argument(
        '-g', '--gui', help='Trigger sending gui messages to the gui client',  action='store_true')

    args = parser.parse_args()
    port = args.port
    address = args.address
    gui = args.gui

    def run(reactor):
        factory = EchoClientFactory(gui)
        reactor.connectTCP(address, port, factory)
        return factory.done

    task.react(run)


if __name__ == '__main__':
    main()
