from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, SendBotMessageAPIView, AnalyseMessageView, BotResponseViewSet, MessageHistoryListView, toggle_bot, BotStatsAPIView, BotRecommendationAPIView, webhook_view

router = DefaultRouter()
router.register(r'intentions', BotResponseViewSet, basename='botresponse')
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
path('send-message/', SendBotMessageAPIView.as_view(), name='send_whatsapp_message'),
path('analyse-message/', AnalyseMessageView.as_view(), name='analyse_message'),
path('messages-history/', MessageHistoryListView.as_view(), name='messages_history'),
path('recommandation/', BotRecommendationAPIView.as_view(), name='bot_recommendation'),
path('toggle-bot/', toggle_bot, name='toggle_bot'),
path('stats/', BotStatsAPIView.as_view(), name='bot_stats'),
path('webhook/', webhook_view, name='webhook'),
path('', include(router.urls)),

]
