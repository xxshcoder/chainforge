# ============================================
# FILE: blockchain/blockchain.py (ENHANCED VERSION)
# ============================================

from django.utils import timezone
from datetime import timedelta
from .models import Block, Transaction


class Blockchain:
    DIFFICULTY = 4
    MINING_REWARD = 10
    
    # Auto-adjustment settings
    TARGET_BLOCK_TIME = 10  # Target: 10 seconds per block
    ADJUSTMENT_INTERVAL = 5  # Adjust difficulty every 5 blocks
    
    @classmethod
    def set_difficulty(cls, new_difficulty):
        """Change mining difficulty dynamically"""
        if new_difficulty < 1 or new_difficulty > 10:
            return False, "Difficulty must be between 1 and 10"
        cls.DIFFICULTY = new_difficulty
        return True, f"Difficulty set to {new_difficulty}"
    
    @classmethod
    def get_difficulty(cls):
        """Get current mining difficulty"""
        return cls.DIFFICULTY
    
    @classmethod
    def adjust_difficulty(cls):
        """
        Auto-adjust difficulty based on recent mining times (Bitcoin-style)
        Adjusts every ADJUSTMENT_INTERVAL blocks
        """
        latest_block = cls.get_latest_block()
        
        if not latest_block or latest_block.index < cls.ADJUSTMENT_INTERVAL:
            return False, "Not enough blocks to adjust difficulty", cls.DIFFICULTY
        
        # Check if we're at an adjustment point
        if (latest_block.index + 1) % cls.ADJUSTMENT_INTERVAL != 0:
            return False, "Not at adjustment interval", cls.DIFFICULTY
        
        # Get the last ADJUSTMENT_INTERVAL blocks
        blocks = Block.objects.order_by('-index')[:cls.ADJUSTMENT_INTERVAL]
        blocks = list(reversed(blocks))
        
        if len(blocks) < cls.ADJUSTMENT_INTERVAL:
            return False, "Not enough blocks", cls.DIFFICULTY
        
        # Calculate actual time taken for these blocks
        time_taken = (blocks[-1].timestamp - blocks[0].timestamp).total_seconds()
        
        # Calculate expected time
        expected_time = cls.TARGET_BLOCK_TIME * (cls.ADJUSTMENT_INTERVAL - 1)
        
        # Calculate adjustment ratio
        if expected_time == 0:
            return False, "Invalid time calculation", cls.DIFFICULTY
        
        ratio = time_taken / expected_time
        
        old_difficulty = cls.DIFFICULTY
        
        # Adjust difficulty based on ratio
        if ratio < 0.5:
            # Mining too fast - increase difficulty
            cls.DIFFICULTY = min(10, cls.DIFFICULTY + 1)
            reason = "increased (blocks mined too fast)"
        elif ratio > 2.0:
            # Mining too slow - decrease difficulty
            cls.DIFFICULTY = max(1, cls.DIFFICULTY - 1)
            reason = "decreased (blocks mined too slow)"
        else:
            # Within acceptable range - no change
            return False, "Difficulty unchanged (mining time acceptable)", cls.DIFFICULTY
        
        adjustment_info = {
            'adjusted': True,
            'old_difficulty': old_difficulty,
            'new_difficulty': cls.DIFFICULTY,
            'reason': reason,
            'blocks_analyzed': cls.ADJUSTMENT_INTERVAL,
            'actual_time': round(time_taken, 2),
            'expected_time': round(expected_time, 2),
            'ratio': round(ratio, 2)
        }
        
        return True, f"Difficulty {reason}", adjustment_info
    
    @staticmethod
    def create_genesis_block():
        """Create the first block in the chain"""
        genesis = Block(
            index=0,
            timestamp=timezone.now(),
            data={'message': 'Genesis Block - ChainForge Initialized'},
            previous_hash='0',
            nonce=0
        )
        genesis.hash = genesis.calculate_hash()
        genesis.save()
        return genesis
    
    @staticmethod
    def get_latest_block():
        """Get the most recent block"""
        return Block.objects.order_by('-index').first()
    
    @staticmethod
    def add_block(data):
        """Add a new block to the chain"""
        latest_block = Blockchain.get_latest_block()
        
        if not latest_block:
            return Blockchain.create_genesis_block()
        
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=timezone.now(),
            data=data,
            previous_hash=latest_block.hash,
            nonce=0
        )
        
        new_block.hash = new_block.calculate_hash()
        new_block.mine_block(Blockchain.DIFFICULTY)
        new_block.save()
        
        return new_block
    
    @staticmethod
    def validate_chain():
        """Validate the entire blockchain"""
        blocks = Block.objects.all().order_by('index')
        
        for i, block in enumerate(blocks):
            if i == 0:  # Genesis block
                continue
            
            # Check if hash is correct
            if block.hash != block.calculate_hash():
                return False, f"Block {block.index} has invalid hash"
            
            # Check if previous hash matches
            previous_block = blocks[i-1]
            if block.previous_hash != previous_block.hash:
                return False, f"Block {block.index} has invalid previous hash"
        
        return True, "Blockchain is valid"
    
    @staticmethod
    def mine_pending_transactions(mining_reward_address, auto_adjust=True):
        """
        Mine all pending transactions into a new block
        Auto-adjusts difficulty if enabled
        """
        pending_txs = Transaction.objects.filter(pending=True)
        
        if not pending_txs.exists():
            return None, None
        
        # Create transaction data
        tx_data = {
            'transactions': [tx.to_dict() for tx in pending_txs]
        }
        
        # Add new block
        new_block = Blockchain.add_block(tx_data)
        
        # Update transactions
        pending_txs.update(block=new_block, pending=False)
        
        # Create mining reward transaction
        reward_tx = Transaction(
            sender="SYSTEM",
            receiver=mining_reward_address,
            amount=Blockchain.MINING_REWARD,
            pending=True
        )
        reward_tx.save()
        
        # Auto-adjust difficulty if enabled
        adjustment_info = None
        if auto_adjust:
            adjusted, message, info = Blockchain.adjust_difficulty()
            if adjusted:
                adjustment_info = info
        
        return new_block, adjustment_info
    
    @staticmethod
    def get_mining_stats():
        """Get statistics about mining performance"""
        blocks = Block.objects.order_by('-index')[:10]
        
        if len(blocks) < 2:
            return {
                'total_blocks': Block.objects.count(),
                'current_difficulty': Blockchain.DIFFICULTY,
                'message': 'Not enough blocks for statistics'
            }
        
        blocks = list(reversed(blocks))
        
        # Calculate average time between blocks
        time_diffs = []
        for i in range(1, len(blocks)):
            diff = (blocks[i].timestamp - blocks[i-1].timestamp).total_seconds()
            time_diffs.append(diff)
        
        avg_time = sum(time_diffs) / len(time_diffs) if time_diffs else 0
        
        return {
            'total_blocks': Block.objects.count(),
            'current_difficulty': Blockchain.DIFFICULTY,
            'target_block_time': Blockchain.TARGET_BLOCK_TIME,
            'average_block_time': round(avg_time, 2),
            'last_10_blocks': [round(t, 2) for t in time_diffs],
            'adjustment_interval': Blockchain.ADJUSTMENT_INTERVAL,
            'next_adjustment_at_block': (Block.objects.count() // Blockchain.ADJUSTMENT_INTERVAL + 1) * Blockchain.ADJUSTMENT_INTERVAL
        }