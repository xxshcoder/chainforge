from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views

app_name = 'blockchain'

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('chain/', views.get_chain, name='get_chain'),
    path('validate/', views.validate_chain, name='validate_chain'),
    path('transaction/create/', views.create_transaction, name='create_transaction'),
    path('mine/', views.mine_block, name='mine_block'),
    path('pending-transactions/', views.get_pending_transactions, name='get_pending_transactions'),
    path('initialize/', views.initialize_blockchain, name='initialize_blockchain'),
    path('balance/<str:address>/', views.get_balance, name='get_balance'),
    path('batch-transactions/', views.batch_create_transactions, name='batch_create_transactions'),
    path('batch-mine/', views.batch_mine_blocks, name='batch_mine_blocks'),
    path('simulate/', views.simulate_blockchain, name='simulate_blockchain'),
    path('quick-setup/', views.quick_setup, name='quick_setup'),
    path('summary/', views.get_blockchain_summary, name='get_blockchain_summary'),
    path('reset/', views.reset_blockchain, name='reset_blockchain'),
    path('difficulty/', views.get_difficulty, name='get_difficulty'),
    path('set-difficulty/', views.set_difficulty, name='set_difficulty'),
    path('mining-stats/', views.get_mining_stats, name='get_mining_stats'),
    path('set-target-time/', views.set_target_time, name='set_target_time'),
    path('set-adjustment-interval/', views.set_adjustment_interval, name='set_adjustment_interval'),
    path('adjust-difficulty/', views.manual_adjust_difficulty, name='manual_adjust_difficulty'),
]