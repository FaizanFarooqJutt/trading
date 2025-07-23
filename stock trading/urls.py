from django.urls import path
from home import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='user_logout'),
    path('stock/<int:stock_id>/', views.stock_detail, name='stock_detail'),
    path('get_live_price/<str:symbol>/', views.get_live_price, name='get_live_price'),
    path('get_candlestick_data/<str:symbol>/', views.get_candlestick_data, name='get_candlestick_data'),
    path('transactions/', views.transaction_history, name='transaction_history'),  # ✅ Added
]
