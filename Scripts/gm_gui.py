import tkinter as tk
import json
from twisted.internet import tksupport, reactor
from twisted.internet.protocol import Protocol, ClientFactory
from sys import stdout

# Colors for the gui
colors = {
    'P': 'grey',
    'S': 'grey',
    'R': 'red',
    'B': 'blue',
    'RP': 'red',
    'BP': 'blue',
    'RS': 'red',
    'BS': 'blue',
    'N': 'white',
    'YG': 'yellow',
    'G': 'yellow',
    '': 'white',
    'B|P': 'cyan',
    'R|P': 'pink',
    'B|S': 'cyan',
    'R|S': 'pink'
}

root = tk.Tk()

# Install the Reactor support
tksupport.install(root)

buttons = []


def show(msg):
    board = msg['board']

    r = 0
    i = 0
    for row in board:
        c = 0
        for cell in row:
            t = cell
            col = colors[t]
            if len(buttons) <= i:
                btn = tk.Button(root, text=t, bg=col, height=5, width=10)
                btn.grid(row=len(board) - r, column=c)
                buttons.append(btn)
            else:
                btn = buttons[i]
                btn.config(text=t, bg=col)
            c += 1
            i += 1
        r += 1
                

class Echo(Protocol):
    def connectionMade(self):
        # Send game start message to server
        print('Sending connection message to server')
        self.transport.write(b'gui')

    def dataReceived(self, data):
        # print("Got data.")
        for d in data.split(b'\x17'):
            if d != b'':
                show( json.loads(d) )


class EchoClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        reactor.stop()


host = 'localhost'
port = 9997

reactor.connectTCP(host, port, EchoClientFactory())
reactor.run()