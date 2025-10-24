# ============================================
# FILE: blockchain/tests.py
# ============================================

from django.test import TestCase, Client
from django.urls import reverse
from .models import Block, Transaction
import json

class BlockchainTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.miner_address = "TEST_MINER"
        self.sender = "Alice"
        self.receiver = "Bob"

    # ===========================
    # BASIC ENDPOINT TESTS
    # ===========================
    def test_initialize_blockchain(self):
        url = reverse('blockchain:initialize_blockchain')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('genesis_block', data)
        self.assertEqual(Block.objects.count(), 1)

        # Initialize again should give message
        response2 = self.client.post(url)
        self.assertEqual(response2.status_code, 200)
        self.assertIn('message', response2.json())

    def test_create_transaction_missing_fields(self):
        url = reverse('blockchain:create_transaction')
        response = self.client.post(url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_create_transaction_success(self):
        url = reverse('blockchain:create_transaction')
        payload = {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': 50
        }
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(data['transaction']['sender'], self.sender)

    def test_get_chain(self):
        self.client.post(reverse('blockchain:initialize_blockchain'))
        url = reverse('blockchain:get_chain')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('chain', data)
        self.assertGreaterEqual(len(data['chain']), 1)

    def test_mine_block_no_transactions(self):
        self.client.post(reverse('blockchain:initialize_blockchain'))
        url = reverse('blockchain:mine_block')
        response = self.client.post(url, data=json.dumps({'miner_address': self.miner_address}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())

    def test_get_pending_transactions(self):
        tx = Transaction.objects.create(sender=self.sender, receiver=self.receiver, amount=20, pending=True)
        url = reverse('blockchain:pending_transactions')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('pending_transactions', data)
        self.assertEqual(len(data['pending_transactions']), 1)

    def test_get_balance(self):
        Transaction.objects.create(sender=self.sender, receiver=self.receiver, amount=100, pending=False)
        url = reverse('blockchain:get_balance', args=[self.receiver])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['balance'], '100.00')

    def test_validate_chain(self):
        url = reverse('blockchain:validate_chain')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('valid', response.json())

    # ===========================
    # DIFFICULTY & MINING CONFIGURATION
    # ===========================
    def test_difficulty_endpoints(self):
        url = reverse('blockchain:get_difficulty')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('difficulty', data)

        url_set = reverse('blockchain:set_difficulty')
        response2 = self.client.post(url_set, data=json.dumps({'difficulty': 5}),
                                     content_type='application/json')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['difficulty'], 5)

    def test_mining_stats_and_adjustment_endpoints(self):
        url_stats = reverse('blockchain:get_mining_stats')
        response = self.client.get(url_stats)
        self.assertEqual(response.status_code, 200)

        url_target = reverse('blockchain:set_target_time')
        response2 = self.client.post(url_target, data=json.dumps({'target_time': 15}),
                                     content_type='application/json')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response2.json()['target_block_time'], 15)

        url_interval = reverse('blockchain:set_adjustment_interval')
        response3 = self.client.post(url_interval, data=json.dumps({'interval': 6}),
                                     content_type='application/json')
        self.assertEqual(response3.status_code, 200)
        self.assertEqual(response3.json()['adjustment_interval'], 6)

        url_manual = reverse('blockchain:manual_adjust_difficulty')
        response4 = self.client.post(url_manual, content_type='application/json')
        self.assertEqual(response4.status_code, 200)
        self.assertIn('message', response4.json())

    # ===========================
    # BATCH OPERATIONS
    # ===========================
    def test_batch_create_transactions(self):
        url = reverse('blockchain:batch_create_transactions')
        response = self.client.post(url, data=json.dumps({'count': 10}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['transactions_count'], 10)

    def test_batch_create_transactions_invalid_count(self):
        url = reverse('blockchain:batch_create_transactions')
        response = self.client.post(url, data=json.dumps({'count': 0}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_batch_mine_blocks(self):
        Transaction.objects.create(sender="Alice", receiver="Bob", amount=50, pending=True)
        url = reverse('blockchain:batch_mine_blocks')
        response = self.client.post(url, data=json.dumps({'count': 3, 'miner_address': self.miner_address}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['blocks_mined'], 3)

    # ===========================
    # SIMULATION & QUICK SETUP
    # ===========================
    def test_simulate_blockchain(self):
        url = reverse('blockchain:simulate_blockchain')
        payload = {'blocks': 5, 'transactions_per_block': 3, 'miner_address': self.miner_address}
        response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['summary']['blocks_mined'], 5)
        self.assertGreater(data['summary']['total_transactions'], 0)

    def test_quick_setup(self):
        url = reverse('blockchain:quick_setup')
        response = self.client.post(url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['blockchain_initialized'])
        self.assertGreaterEqual(data['blocks_created'], 1)

    # ===========================
    # RESET & EDGE CASES
    # ===========================
    def test_reset_blockchain(self):
        Transaction.objects.create(sender="Alice", receiver="Bob", amount=100, pending=True)
        Block.objects.create(index=0, previous_hash="0", hash="abc123", data="genesis", nonce=0)

        url = reverse('blockchain:reset_blockchain')

        response = self.client.post(url, data=json.dumps({}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

        response2 = self.client.post(url, data=json.dumps({'confirm': True}), content_type='application/json')
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(Block.objects.count(), 0)
        self.assertEqual(Transaction.objects.count(), 0)

    def test_simulate_invalid_blocks(self):
        url = reverse('blockchain:simulate_blockchain')
        response = self.client.post(url, data=json.dumps({'blocks': 0, 'transactions_per_block': 3}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_simulate_invalid_transactions_per_block(self):
        url = reverse('blockchain:simulate_blockchain')
        response = self.client.post(url, data=json.dumps({'blocks': 5, 'transactions_per_block': 0}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 400)
def test_create_transaction_zero_amount(self):
    url = reverse('blockchain:create_transaction')
    payload = {'sender': 'Alice', 'receiver': 'Bob', 'amount': 0}
    response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(Transaction.objects.first().amount, 0)

def test_create_transaction_negative_amount(self):
    url = reverse('blockchain:create_transaction')
    payload = {'sender': 'Alice', 'receiver': 'Bob', 'amount': -50}
    response = self.client.post(url, data=json.dumps(payload), content_type='application/json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(Transaction.objects.first().amount, -50)
def test_mine_block_no_pending_transactions_message(self):
    url = reverse('blockchain:mine_block')
    response = self.client.post(url, data=json.dumps({'miner_address': 'MinerX'}), content_type='application/json')
    self.assertIn('No pending transactions', response.json()['message'])
def test_manual_adjust_difficulty_no_change(self):
    url = reverse('blockchain:manual_adjust_difficulty')
    response = self.client.post(url, content_type='application/json')
    self.assertIn('current_difficulty', response.json())
def test_batch_create_transactions_max(self):
    url = reverse('blockchain:batch_create_transactions')
    response = self.client.post(url, data=json.dumps({'count': 1000}), content_type='application/json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(Transaction.objects.count(), 1000)
def test_batch_mine_blocks_max(self):
    for i in range(100):  # Add some pending transactions
        Transaction.objects.create(sender='Alice', receiver='Bob', amount=10)
    url = reverse('blockchain:batch_mine_blocks')
    response = self.client.post(url, data=json.dumps({'count': 50, 'miner_address': 'StressMiner'}), content_type='application/json')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()['blocks_mined'], 50)
def test_quick_setup_creates_blocks_and_transactions(self):
    url = reverse('blockchain:quick_setup')
    response = self.client.post(url, content_type='application/json')
    data = response.json()
    self.assertTrue(data['blockchain_initialized'])
    self.assertGreaterEqual(Block.objects.count(), 5)
    self.assertGreater(Transaction.objects.count(), 0)
def test_blockchain_summary_contains_correct_data(self):
    url = reverse('blockchain:get_chain')
    response = self.client.get(url)
    chain_length_before = len(response.json()['chain'])

    # Create transaction and mine block
    Transaction.objects.create(sender='Alice', receiver='Bob', amount=100)
    self.client.post(reverse('blockchain:mine_block'), data=json.dumps({'miner_address': 'MinerY'}), content_type='application/json')

    url_summary = reverse('blockchain:get_chain')
    response2 = self.client.get(url_summary)
    self.assertGreater(len(response2.json()['chain']), chain_length_before)
