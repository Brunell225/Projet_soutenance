from django.contrib import admin
from .models import Product, BotResponse, BotMessageHistory, BotSession, MessageTemplate

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'price', 'is_available', 'product_code')
    list_filter = ('is_available',)
    search_fields = ('name', 'tags', 'user__company_name')
    readonly_fields = ('tags',)

@admin.register(BotResponse)
class BotResponseAdmin(admin.ModelAdmin):
    list_display = ('intent', 'response_preview', 'is_question', 'user')
    list_filter = ('intent', 'is_question')
    search_fields = ('intent', 'response', 'question')
    
    def response_preview(self, obj):
        return obj.response[:50] + '...'

@admin.register(BotMessageHistory)
class BotMessageHistoryAdmin(admin.ModelAdmin):
    list_display = ('client_number', 'timestamp', 'user', 'detected_intent', 'confidence_score')
    list_filter = ('timestamp', 'detected_intent')
    search_fields = ('client_number', 'client_message', 'bot_response')

@admin.register(BotSession)
class BotSessionAdmin(admin.ModelAdmin):
    list_display = ('client_number', 'user', 'current_intent', 'bot_actif', 'last_updated')
    list_filter = ('bot_actif',)
    search_fields = ('client_number', 'current_intent')

@admin.register(MessageTemplate)
class MessageTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'auto_trigger')
    list_filter = ('auto_trigger',)
    search_fields = ('title', 'content')
