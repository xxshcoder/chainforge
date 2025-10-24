# ============================================
# FILE: blockchain/apps.py
# ============================================

from django.apps import AppConfig


class BlockchainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blockchain'
    verbose_name = 'ChainForge Blockchain'