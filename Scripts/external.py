import asyncio
import multipledispatch as md
import threading
import random as rand
import time
import uuid
import pubsub as ps

import common.settings as s
import common.messages as m
import common.delay as d
import common.logger as l

import gm as g

# Abstraction class on top of GM, handles concurrency, logging, knowledge exchange and communication with the outside world

# Additional function used to start the event loop
def start_worker(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


class GmExternal:

    # Initializes the class and sets up the necessary pub/sub communication

    def __init__(self, server_callback, gui_callback):
        # Subscribe callbacks to the relavant topics
        ps.pub.subscribe(server_callback, 'server')
        ps.pub.subscribe(gui_callback, 'gui')

        # Init settings
        settings = s.Settings()

        # Init gm
        self.gm = g.GM(settings)
        self.wait_time = settings.new_piece_freq

        # Init logger
        self.logger = l.Logger(settings.game_name)

        # Sets up executing gm tasks in separate thread asynchronously
        self.worker_loop = asyncio.new_event_loop()
        self.worker = threading.Thread(
            target=start_worker, args=(self.worker_loop,))
        self.worker.daemon = True
        self.worker.start()

        # Storages for handling knowledge exchange requests
        self.exchange_storage = []
        self.disabled_exchanges = []

        # Subscribe to relevant messages
        ps.pub.subscribe(self.end_game, 'end_internal')
        ps.pub.subscribe(self.start_pieces, 'start-pieces')

    # Knowledge exchange functions

    # Stores new exchange in the register
    def register_exchange(self, msg: m.AuthorizeKnowledgeExchange):
        pl_to = self.gm.get_player(msg.receiverGuid)

        # If recipient is unknown
        if pl_to is None:
            self.disabled_exchanges.append({
                "from": msg.userGuid,
                "to": msg.receiverGuid
            })
            rej_msg = m.RejectKnowledgeExchange(
                id=msg.id, rejectDuration='permanent')
            self.relay_exchange(rej_msg)
            return

        # Check if permanently rejected
        for r in self.disabled_exchanges:
            if r['from'] == msg.id:
                rej_msg = m.RejectKnowledgeExchange(
                    id=msg.id, rejectDuration='permanent')
                self.relay_exchange(rej_msg)
                return

        # If allowed, store exchange and relay to player
        reg = {
            "from": msg.userGuid,
            "to": msg.receiverGuid,
            "authorized": False,
            "data_from": None,
            "data_to": None
        }
        self.exchange_storage.append(reg)
        self.relay_exchange(msg)

    # Pass directly to server without passing to internal gm
    def relay_exchange(self, msg):
        ps.pub.sendMessage('server', arg1=msg)

    def store_knowledge_data(self, msg: m.KnowledgeExchangeData):
        # Find correct register
        for r in self.exchange_storage:
            # If data from requester
            if msg.id == r["from"] and msg.to == r["to"]:
                r['data_from'] = msg.fields

            # If data from responder
            if msg.id == r["to"] and msg.to == r["from"]:
                r['data_to'] = msg.fields

    def deregister_exchange(self, msg: m.RejectKnowledgeExchange):
        for r in self.exchange_storage:
            # If single, remove from register
            if msg.rejectDuration == 'single':
                self.exchange_storage.remove(r)
                return
            # If permanent, store
            else:
                self.disabled_exchanges.append({
                    "from": r['from'],
                    "to": r['to']
                })

    def pass_exchange_data(self, msg: m.AcceptKnowledgeExchange):

        # Locate which exchange to pass
        for r in self.exchange_storage:
            # Pass data to both players
            if r['to'] == msg.id:
                # Msg setup
                data_from = m.KnowledgeExchangeData(
                    id=r['from'], to=r['to'], fields=r['data_from'])
                data_to = m.KnowledgeExchangeData(
                    id=r['to'], to=r['from'], fields=r['data_to'])

                # Relay data messages
                self.relay_exchange(data_from)
                self.relay_exchange(data_to)

                # Deregister exchange, since it is complete
                self.exchange_storage.remove(r)
                return

    # Starts adding pieces based on the frequency in settings
    def start_pieces(self):
        self.worker_loop.call_later(self.wait_time, self._start_pieces)

    def _start_pieces(self):
        self.gm.add_new_piece()
        self.start_pieces()

    # Stops worker thread and saves log
    def end_game(self, msg):
        self.worker_loop.stop()
        self.logger.save_log()

    # Wrapper for _send_message(), calls the _send_message() function in worker thread and logs message
    def send_message(self, msg):
        # Log message
        player = self.gm.get_player(msg.id)
        self.logger.log(msg, player)

        # Add sending message to the worker thread's event loop
        self.worker_loop.call_soon_threadsafe(self._send_message, msg)

    # This is python's closest equivalent to method overloading :(

    @md.dispatch(m.JoinGame)
    def _send_message(self, msg):
        self.worker_loop.call_later(0, self.gm.join_game, msg)

    @md.dispatch(m.Move)
    def _send_message(self, msg):
        self.worker_loop.call_later(d.Delay.MOVE, self.gm.move_player, msg)

    @md.dispatch(m.Discover)
    def _send_message(self, msg):
        self.worker_loop.call_later(d.Delay.DISCOVER, self.gm.discover, msg)

    @md.dispatch(m.TestPiece)
    def _send_message(self, msg):
        self.worker_loop.call_later(d.Delay.TEST, self.gm.test_piece, msg)

    @md.dispatch(m.PickUp)
    def _send_message(self, msg):
        self.worker_loop.call_later(
            d.Delay.PICKUP, self.gm.player_pick_up, msg)

    @md.dispatch(m.PlacePiece)
    def _send_message(self, msg):
        self.worker_loop.call_later(d.Delay.PLACE, self.gm.place_piece, msg)

    @md.dispatch(m.DestroyPiece)
    def _send_message(self, msg):
        self.worker_loop.call_later(
            d.Delay.DESTROY, self.gm.destroy_piece, msg)

    # Knowledge exchange

    @md.dispatch(m.AuthorizeKnowledgeExchange)
    def _send_message(self, msg):
        self.register_exchange(msg)

    @md.dispatch(m.KnowledgeExchangeData)
    def _send_message(self, msg):
        self.store_knowledge_data(msg)

    @md.dispatch(m.RejectKnowledgeExchange)
    def _send_message(self, msg):
        self.deregister_exchange(msg)
        self.relay_exchange(msg)

    @md.dispatch(m.AcceptKnowledgeExchange)
    def _send_message(self, msg):
        self.worker_loop.call_later(
            d.Delay.KNOWLEDGE, self.pass_exchange_data, msg)
