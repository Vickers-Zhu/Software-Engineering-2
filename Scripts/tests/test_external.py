import unittest
import uuid

import env

import external
import common.messages as m
import common.player as player

# Pretend server callback function
current_msg = None

def server(arg1):
    global current_msg
    current_msg = arg1


def gui_callback(arg1):
    pass


class ExternalTest(unittest.TestCase):

    def setUp(self):
        global current_msg
        self.external = external.GmExternal(server, gui_callback)

    def test_register_exchange(self):
        # Add recipient to game
        pl_to = player.GmPlayer(id=uuid.uuid4(), team='red')
        self.external.gm.join_game(m.JoinGame(
            id=pl_to.id, preferred_team='red', type='player'))

        # Allowed
        msg = m.AuthorizeKnowledgeExchange(userGuid=uuid.uuid4(),
                                           receiverGuid=pl_to.id)

        self.external.register_exchange(msg)

        # Check that the exchange was added
        self.assertEqual(len(self.external.exchange_storage), 1)

        # Check that the message was relayed
        from_id = current_msg.userGuid
        self.assertEqual(from_id, msg.userGuid)

    def test_storing_knowledge_data(self):
        # Add recipient to game
        pl_to = player.GmPlayer(id=uuid.uuid4(), team='red')
        self.external.gm.join_game(m.JoinGame(
            id=pl_to.id, preferred_team='red', type='player'))

        msg = m.KnowledgeExchangeData(
            id=uuid.uuid4(), to=pl_to.id, fields=[])

        self.external.store_knowledge_data(msg)

        # Don't store if unknown exchange
        self.assertEqual(len(self.external.exchange_storage), 0)

        # Init exchange
        from_id = uuid.uuid4()
        to_id = pl_to.id
        msg = m.AuthorizeKnowledgeExchange(userGuid=from_id,
                                           receiverGuid=to_id)

        self.external.register_exchange(msg)

        msg = m.KnowledgeExchangeData(
            id=uuid.uuid4(), to=uuid.uuid4(), fields=[])

        self.external.store_knowledge_data(msg)

        # Check that the data is stored
        self.assertEqual(len(self.external.exchange_storage), 1)

    def test_deregister_exchange(self):
        # Add recipient to game
        pl_to = player.GmPlayer(id=uuid.uuid4(), team='red')
        self.external.gm.join_game(m.JoinGame(
            id=pl_to.id, preferred_team='red', type='player'))


        # Init exchange
        from_id = uuid.uuid4()
        to_id = pl_to.id
        msg = m.AuthorizeKnowledgeExchange(userGuid=from_id,
                                           receiverGuid=to_id)

        self.external.register_exchange(msg)

        # Reject exchange, single
        msg = m.RejectKnowledgeExchange(id=from_id, rejectDuration='single')
        self.external.deregister_exchange(msg)

        # Check that it has been removed
        self.assertEqual(len(self.external.exchange_storage), 0)

        # Init exchange
        msg = m.AuthorizeKnowledgeExchange(userGuid=from_id,
                                           receiverGuid=to_id)

        self.external.register_exchange(msg)

        # Reject exchange, permanent
        msg = m.RejectKnowledgeExchange(id=from_id, rejectDuration='permanent')
        self.external.deregister_exchange(msg)

        # Check that it has been added to permanent exclusion
        self.assertEqual(len(self.external.disabled_exchanges), 1)


if __name__ == '__main__':
    unittest.main(exit=False)
