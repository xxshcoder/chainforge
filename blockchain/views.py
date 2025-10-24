from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdminUser
from rest_framework import serializers
from decimal import Decimal
from django_ratelimit.decorators import ratelimit
import json
import random
from django.db import transaction as db_transaction
from .models import Block, Transaction
from .blockchain import Blockchain
import logging

logger = logging.getLogger(__name__)

# Serializers for input validation
class TransactionSerializer(serializers.Serializer):
    sender = serializers.CharField(max_length=100)
    receiver = serializers.CharField(max_length=100)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))

class MineBlockSerializer(serializers.Serializer):
    miner_address = serializers.CharField(max_length=100)

class BatchTransactionsSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=1000)

class BatchMineBlocksSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=50)
    miner_address = serializers.CharField(max_length=100, required=False, default='BatchMiner')
    auto_adjust = serializers.BooleanField(default=True)

class SimulateBlockchainSerializer(serializers.Serializer):
    blocks = serializers.IntegerField(min_value=1, max_value=100)
    transactions_per_block = serializers.IntegerField(min_value=1, max_value=50)
    miner_address = serializers.CharField(max_length=100, required=False, default='Simulator')

class SetDifficultySerializer(serializers.Serializer):
    difficulty = serializers.IntegerField(min_value=1)

class SetTargetTimeSerializer(serializers.Serializer):
    target_time = serializers.IntegerField(min_value=1, max_value=300)

class SetAdjustmentIntervalSerializer(serializers.Serializer):
    interval = serializers.IntegerField(min_value=1, max_value=100)

class ResetBlockchainSerializer(serializers.Serializer):
    confirm = serializers.BooleanField()

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def get_chain(request):
    """Get the entire blockchain"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for get_chain by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        blocks = Block.objects.all()
        chain_data = [
            {
                'index': block.index,
                'timestamp': block.timestamp.isoformat(),
                'data': block.data,
                'previous_hash': block.previous_hash,
                'hash': block.hash,
                'nonce': block.nonce
            }
            for block in blocks
        ]
        return JsonResponse({
            'chain': chain_data,
            'length': len(chain_data)
        })
    except Exception as e:
        logger.error(f"Error in get_chain for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def validate_chain(request):
    """Validate the blockchain"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for validate_chain by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        is_valid, message = Blockchain.validate_chain()
        return JsonResponse({
            'valid': is_valid,
            'message': message
        })
    except Exception as e:
        logger.error(f"Error in validate_chain for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='50/m', method='POST', block=True)
def create_transaction(request):
    """Create a new transaction"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for create_transaction by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = TransactionSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        data = serializer.validated_data
        transaction = Transaction(
            sender=data['sender'],
            receiver=data['receiver'],
            amount=data['amount']
        )
        transaction.save()
        logger.info(f"Transaction created by {request.user.username}: {transaction.id}")
        return JsonResponse({
            'message': 'Transaction created successfully',
            'transaction': {
                'id': transaction.id,
                'sender': transaction.sender,
                'receiver': transaction.receiver,
                'amount': str(transaction.amount)
            }
        })
    except Exception as e:
        logger.error(f"Error in create_transaction for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='5/m', method='POST', block=True)
def mine_block(request):
    """Mine pending transactions"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for mine_block by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = MineBlockSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        miner_address = serializer.validated_data['miner_address']
        if not miner_address.isalnum():
            return JsonResponse({'error': 'Invalid miner address'}, status=400)
        
        result = Blockchain.mine_pending_transactions(miner_address)
        if result is None:
            return JsonResponse({'message': 'No pending transactions to mine'})
        
        new_block, adjustment_info = result if isinstance(result, tuple) else (result, None)
        if not new_block:
            return JsonResponse({'message': 'No block mined'})
        
        logger.info(f"Block mined by {request.user.username}: index={new_block.index}")
        return JsonResponse({
            'message': 'Block mined successfully',
            'block': {
                'index': getattr(new_block, 'index', None),
                'hash': getattr(new_block, 'hash', None),
                'transactions': new_block.transactions.count() if hasattr(new_block, 'transactions') else 0,
            },
            'difficulty_adjustment': adjustment_info,
        })
    except Exception as e:
        logger.error(f"Error in mine_block for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def get_pending_transactions(request):
    """Get all pending transactions"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for get_pending_transactions by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        pending = Transaction.objects.filter(pending=True)
        transactions = [
            {
                'id': tx.id,
                'sender': tx.sender,
                'receiver': tx.receiver,
                'amount': str(tx.amount),
                'timestamp': tx.timestamp.isoformat()
            }
            for tx in pending
        ]
        return JsonResponse({'pending_transactions': transactions})
    except Exception as e:
        logger.error(f"Error in get_pending_transactions for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def initialize_blockchain(request):
    """Initialize blockchain with genesis block"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for initialize_blockchain by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        if Block.objects.exists():
            return JsonResponse({'message': 'Blockchain already initialized'})
        
        genesis = Blockchain.create_genesis_block()
        logger.info(f"Blockchain initialized by {request.user.username}")
        return JsonResponse({
            'message': 'Blockchain initialized with genesis block',
            'genesis_block': {
                'index': genesis.index,
                'hash': genesis.hash
            }
        })
    except Exception as e:
        logger.error(f"Error in initialize_blockchain for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def get_balance(request, address):
    """Get balance for a specific address"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for get_balance by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        transactions = Transaction.objects.filter(pending=False)
        balance = 0
        for tx in transactions:
            if tx.receiver == address:
                balance += tx.amount
            if tx.sender == address:
                balance -= tx.amount
        return JsonResponse({
            'address': address,
            'balance': str(balance)
        })
    except Exception as e:
        logger.error(f"Error in get_balance for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='50/m', method='POST', block=True)
def batch_create_transactions(request):
    """Create multiple transactions at once"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for batch_create_transactions by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = BatchTransactionsSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        count = serializer.validated_data['count']
        names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry', 
                 'Ivy', 'Jack', 'Kate', 'Leo', 'Mary', 'Nathan', 'Olivia', 'Peter',
                 'Quinn', 'Rachel', 'Sam', 'Tina', 'Uma', 'Victor', 'Wendy', 'Xavier',
                 'Yara', 'Zack']
        
        transactions_created = []
        with db_transaction.atomic():
            for i in range(count):
                sender = random.choice(names)
                receiver = random.choice([n for n in names if n != sender])
                amount = round(random.uniform(10, 500), 2)
                tx = Transaction(sender=sender, receiver=receiver, amount=amount)
                tx.save()
                transactions_created.append({
                    'id': tx.id,
                    'sender': sender,
                    'receiver': receiver,
                    'amount': str(amount)
                })
        
        logger.info(f"{count} transactions created by {request.user.username}")
        return JsonResponse({
            'message': f'{count} transactions created successfully',
            'transactions_count': count,
            'sample_transactions': transactions_created[:5]
        })
    except Exception as e:
        logger.error(f"Error in batch_create_transactions for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='5/m', method='POST', block=True)
def batch_mine_blocks(request):
    """Mine multiple blocks in sequence"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for batch_mine_blocks by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = BatchMineBlocksSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        data = serializer.validated_data
        count = data['count']
        miner_address = data['miner_address']
        auto_adjust = data['auto_adjust']
        
        blocks_mined = []
        adjustments = []
        for i in range(count):
            pending_count = Transaction.objects.filter(pending=True).count()
            if pending_count == 0:
                for j in range(random.randint(3, 8)):
                    names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve']
                    sender = random.choice(names)
                    receiver = random.choice([n for n in names if n != sender])
                    amount = round(random.uniform(10, 200), 2)
                    Transaction.objects.create(sender=sender, receiver=receiver, amount=amount)
            
            new_block, adjustment_info = Blockchain.mine_pending_transactions(miner_address, auto_adjust)
            if new_block:
                block_info = {
                    'index': new_block.index,
                    'hash': new_block.hash[:20] + '...',
                    'nonce': new_block.nonce,
                    'transactions': new_block.transactions.count(),
                    'difficulty': Blockchain.DIFFICULTY,
                    'timestamp': new_block.timestamp.isoformat()
                }
                blocks_mined.append(block_info)
                if adjustment_info:
                    adjustments.append({
                        'at_block': new_block.index,
                        'adjustment': adjustment_info
                    })
        
        logger.info(f"{len(blocks_mined)} blocks mined by {request.user.username}")
        return JsonResponse({
            'message': f'{len(blocks_mined)} blocks mined successfully',
            'blocks_mined': len(blocks_mined),
            'blocks': blocks_mined,
            'difficulty_adjustments': adjustments,
            'final_difficulty': Blockchain.DIFFICULTY
        })
    except Exception as e:
        logger.error(f"Error in batch_mine_blocks for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='5/m', method='POST', block=True)
def simulate_blockchain(request):
    """Simulate a complete blockchain with multiple blocks"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for simulate_blockchain by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = SimulateBlockchainSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        data = serializer.validated_data
        num_blocks = data['blocks']
        tx_per_block = data['transactions_per_block']
        miner_address = data['miner_address']
        
        simulation_results = {
            'blocks_created': [],
            'difficulty_changes': [],
            'total_transactions': 0
        }
        names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace', 'Henry']
        
        for block_num in range(num_blocks):
            for _ in range(tx_per_block):
                sender = random.choice(names)
                receiver = random.choice([n for n in names if n != sender])
                amount = round(random.uniform(10, 500), 2)
                Transaction.objects.create(sender=sender, receiver=receiver, amount=amount)
                simulation_results['total_transactions'] += 1
            
            new_block, adjustment_info = Blockchain.mine_pending_transactions(miner_address, auto_adjust=True)
            if new_block:
                simulation_results['blocks_created'].append({
                    'index': new_block.index,
                    'hash': new_block.hash[:16] + '...',
                    'transactions': new_block.transactions.count(),
                    'difficulty': Blockchain.DIFFICULTY,
                    'nonce': new_block.nonce
                })
                if adjustment_info:
                    simulation_results['difficulty_changes'].append({
                        'at_block': new_block.index,
                        'old_difficulty': adjustment_info['old_difficulty'],
                        'new_difficulty': adjustment_info['new_difficulty'],
                        'reason': adjustment_info['reason']
                    })
        
        logger.info(f"Blockchain simulation completed by {request.user.username}: {num_blocks} blocks")
        return JsonResponse({
            'message': f'Simulation complete: {num_blocks} blocks created',
            'summary': {
                'blocks_mined': len(simulation_results['blocks_created']),
                'total_transactions': simulation_results['total_transactions'],
                'difficulty_adjustments': len(simulation_results['difficulty_changes']),
                'final_difficulty': Blockchain.DIFFICULTY
            },
            'details': simulation_results
        })
    except Exception as e:
        logger.error(f"Error in simulate_blockchain for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def quick_setup(request):
    """Quick setup: Initialize blockchain and create several blocks instantly"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for quick_setup by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        if not Block.objects.exists():
            Blockchain.create_genesis_block()
        
        names = ['Alice', 'Bob', 'Charlie', 'David', 'Eve', 'Frank', 'Grace']
        for _ in range(20):
            sender = random.choice(names)
            receiver = random.choice([n for n in names if n != sender])
            amount = round(random.uniform(10, 500), 2)
            Transaction.objects.create(sender=sender, receiver=receiver, amount=amount)
        
        blocks = []
        for i in range(5):
            new_block, _ = Blockchain.mine_pending_transactions('QuickSetupMiner', auto_adjust=True)
            if new_block:
                blocks.append({
                    'index': new_block.index,
                    'hash': new_block.hash[:16] + '...'
                })
        
        logger.info(f"Quick setup completed by {request.user.username}")
        return JsonResponse({
            'message': 'Quick setup complete!',
            'blockchain_initialized': True,
            'blocks_created': len(blocks),
            'blocks': blocks,
            'current_difficulty': Blockchain.DIFFICULTY,
            'total_blocks': Block.objects.count()
        })
    except Exception as e:
        logger.error(f"Error in quick_setup for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def get_blockchain_summary(request):
    """Get a summary of the entire blockchain"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for get_blockchain_summary by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        total_blocks = Block.objects.count()
        total_transactions = Transaction.objects.count()
        pending_transactions = Transaction.objects.filter(pending=True).count()
        completed_transactions = Transaction.objects.filter(pending=False).count()
        
        recent_blocks = Block.objects.order_by('-index')[:10]
        blocks_data = [
            {
                'index': block.index,
                'hash': block.hash[:16] + '...',
                'transactions': block.transactions.count(),
                'timestamp': block.timestamp.isoformat(),
                'nonce': block.nonce
            }
            for block in recent_blocks
        ]
        
        completed_txs = Transaction.objects.filter(pending=False).exclude(sender='SYSTEM')
        total_value = sum([tx.amount for tx in completed_txs])
        
        return JsonResponse({
            'summary': {
                'total_blocks': total_blocks,
                'total_transactions': total_transactions,
                'pending_transactions': pending_transactions,
                'completed_transactions': completed_transactions,
                'total_value_transferred': str(total_value),
                'current_difficulty': Blockchain.DIFFICULTY
            },
            'recent_blocks': blocks_data,
            'mining_stats': Blockchain.get_mining_stats()
        })
    except Exception as e:
        logger.error(f"Error in get_blockchain_summary for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def reset_blockchain(request):
    """Reset the blockchain - DELETE ALL DATA"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for reset_blockchain by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = ResetBlockchainSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        if not serializer.validated_data['confirm']:
            return JsonResponse({'error': 'Please confirm by sending {"confirm": true}'}, status=400)
        
        Block.objects.all().delete()
        Transaction.objects.all().delete()
        Blockchain.DIFFICULTY = 4
        logger.info(f"Blockchain reset by {request.user.username}")
        return JsonResponse({
            'message': 'Blockchain reset successfully',
            'blocks_deleted': True,
            'transactions_deleted': True,
            'difficulty_reset': 4
        })
    except Exception as e:
        logger.error(f"Error in reset_blockchain for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def get_difficulty(request):
    """Get current mining difficulty"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for get_difficulty by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        return JsonResponse({
            'difficulty': Blockchain.get_difficulty(),
            'target_block_time': Blockchain.TARGET_BLOCK_TIME,
            'adjustment_interval': Blockchain.ADJUSTMENT_INTERVAL
        })
    except Exception as e:
        logger.error(f"Error in get_difficulty for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def set_difficulty(request):
    """Set mining difficulty manually"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for set_difficulty by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = SetDifficultySerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        new_difficulty = serializer.validated_data['difficulty']
        success, message = Blockchain.set_difficulty(new_difficulty)
        logger.info(f"Difficulty set to {new_difficulty} by {request.user.username}")
        if success:
            return JsonResponse({
                'message': message,
                'difficulty': Blockchain.DIFFICULTY
            })
        else:
            return JsonResponse({'error': message}, status=400)
    except Exception as e:
        logger.error(f"Error in set_difficulty for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate='100/m', method='GET', block=True)
def get_mining_stats(request):
    """Get mining statistics"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for get_mining_stats by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        stats = Blockchain.get_mining_stats()
        return JsonResponse(stats)
    except Exception as e:
        logger.error(f"Error in get_mining_stats for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def set_target_time(request):
    """Set target block time for auto-adjustment"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for set_target_time by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = SetTargetTimeSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        target_time = serializer.validated_data['target_time']
        Blockchain.TARGET_BLOCK_TIME = target_time
        logger.info(f"Target block time set to {target_time} by {request.user.username}")
        return JsonResponse({
            'message': f'Target block time set to {target_time} seconds',
            'target_block_time': Blockchain.TARGET_BLOCK_TIME
        })
    except Exception as e:
        logger.error(f"Error in set_target_time for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def set_adjustment_interval(request):
    """Set adjustment interval for difficulty changes"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for set_adjustment_interval by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        serializer = SetAdjustmentIntervalSerializer(data=json.loads(request.body))
        if not serializer.is_valid():
            return JsonResponse({'error': serializer.errors}, status=400)
        
        interval = serializer.validated_data['interval']
        Blockchain.ADJUSTMENT_INTERVAL = interval
        logger.info(f"Adjustment interval set to {interval} by {request.user.username}")
        return JsonResponse({
            'message': f'Adjustment interval set to {interval} blocks',
            'adjustment_interval': Blockchain.ADJUSTMENT_INTERVAL
        })
    except Exception as e:
        logger.error(f"Error in set_adjustment_interval for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAdminUser])
@ratelimit(key='user', rate='2/m', method='POST', block=True)
def manual_adjust_difficulty(request):
    """Manually trigger difficulty adjustment"""
    try:
        if getattr(request, 'limited', False):
            logger.warning(f"Rate limit exceeded for manual_adjust_difficulty by user {request.user.username}")
            return JsonResponse({'error': 'Too many requests'}, status=429)
        
        adjusted, message, info = Blockchain.adjust_difficulty()
        logger.info(f"Difficulty adjustment triggered by {request.user.username}")
        if adjusted:
            return JsonResponse({
                'message': message,
                'adjustment_info': info
            })
        else:
            return JsonResponse({
                'message': message,
                'current_difficulty': info
            })
    except Exception as e:
        logger.error(f"Error in manual_adjust_difficulty for {request.user.username}: {str(e)}")
        return JsonResponse({'error': 'An unexpected error occurred'}, status=500)