# ============================================
# FILE: blockchain/models.py
# ============================================

from django.db import models
from django.utils import timezone
import hashlib
import json


class Block(models.Model):
    index = models.IntegerField()
    timestamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField()
    previous_hash = models.CharField(max_length=64)
    nonce = models.IntegerField(default=0)
    hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        ordering = ['index']
    
    def __str__(self):
        return f"Block {self.index} - {self.hash[:10]}..."
    
    def calculate_hash(self):
        """Calculate SHA-256 hash of block contents"""
        block_content = f"{self.index}{self.timestamp}{json.dumps(self.data)}{self.previous_hash}{self.nonce}"
        return hashlib.sha256(block_content.encode()).hexdigest()
    
    def mine_block(self, difficulty=4):
        """Proof of Work - mine block with given difficulty"""
        target = '0' * difficulty
        while self.hash[:difficulty] != target:
            self.nonce += 1
            self.hash = self.calculate_hash()
        return self.hash


class Transaction(models.Model):
    sender = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(default=timezone.now)
    block = models.ForeignKey(Block, on_delete=models.CASCADE, null=True, blank=True, related_name='transactions')
    pending = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.amount}"
    
    def to_dict(self):
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': str(self.amount),
            'timestamp': self.timestamp.isoformat()
        }