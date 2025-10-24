# ============================================
# FILE: blockchain/admin.py
# ============================================

from django.contrib import admin
from .models import Block, Transaction


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['index', 'timestamp', 'hash_short', 'previous_hash_short', 'nonce']
    readonly_fields = ['index', 'timestamp', 'hash', 'previous_hash', 'nonce', 'data']
    ordering = ['-index']
    
    def hash_short(self, obj):
        return f"{obj.hash[:16]}..."
    hash_short.short_description = 'Hash'
    
    def previous_hash_short(self, obj):
        return f"{obj.previous_hash[:16]}..."
    previous_hash_short.short_description = 'Previous Hash'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'amount', 'timestamp', 'pending', 'block']
    list_filter = ['pending', 'timestamp']
    search_fields = ['sender', 'receiver']
    ordering = ['-timestamp']