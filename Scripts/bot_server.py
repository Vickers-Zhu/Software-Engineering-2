
from twisted.internet import task
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineReceiver
import argparse

import common.messages as m
import bot as b
import uuid


class BotServer(LineReceiver):

	def __init__(self):
		self.bot = None
		self.id = uuid.uuid4()
		self.delimiter = b'\x17'

	def connectionMade(self):
		global team
		msg = m.JoinGame(id=self.id, preferred_team=team, type='player')
		self.bot = b.Bot(id = self.id, teamPref = team, callback = self.pass_to_server)
		self.pass_to_server(msg)

	def write_msg(self, msg: m.Message):
		self.transport.write(msg.to_json().encode() + self.delimiter)

	def pass_to_server(self, arg1):
		print(f'> bot server: sending msg to server: {arg1}')
		self.write_msg(arg1)

	def lineReceived(self, line):
		print(f'> bot server: received line \"{line}\"')
		# Translate json to msg
		msg, err = m.Message.from_json_player(line)

		# If the message could not be translated
		if err is not None:
			print(f'> bot server: Could not translate line \n \"{err}\"')
			self.write_msg(m.MessageTranslationError(err))
			return

		# only pass messages directly addressed to the bot
		if type(msg) is not m.GameOver:
			if msg.id is None or msg.id != self.id.hex:
				return

		# pass message to callback function
		if type(msg) is m.ConfirmJoiningGame and msg.result == "denied":
			print(f"bot {self.id} denied from joining the game")
			self.severConnection()
		elif type(msg) is m.GameOver:
			print(f"the game has ended for me: {self.id}")
			self.severConnection()
		else:
			self.bot.interpret_message(msg)

	def severConnection(self):
		print('> bot server: Closing connection')
		self.transport.loseConnection()

	def rawDataReceived(self, data):  # not important, just needs to be implemented
		pass


class EchoClientFactory(ClientFactory):  # no need to change anything there
	protocol = BotServer

	def __init__(self):
		self.done = Deferred()

	def clientConnectionFailed(self, connector, reason):
		print('> bot factory: Connection failed -> ', reason.getErrorMessage())
		self.done.errback(reason)

	def clientConnectionLost(self, connector, reason):
		print('> bot factory: Connection lost -> ', reason.getErrorMessage())
		self.done.callback(None)


team = None


def main():
	global team
	parser = argparse.ArgumentParser()
	parser.add_argument('-a', '--address', help='IPv4 or address or IPv6 address or host name', default='localhost')
	parser.add_argument('-p', '--port', help='Server port number', type=int, default=9997)
	parser.add_argument('-t', '--team', help="Preferred team", type=str, default="red")

	args = parser.parse_args()
	port = args.port
	address = args.address
	team = args.team

	def run(reactor):
		factory = EchoClientFactory()
		reactor.connectTCP(address, port, factory)
		return factory.done

	task.react(run)


if __name__ == "__main__":
	main()