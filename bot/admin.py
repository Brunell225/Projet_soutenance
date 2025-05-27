from django.contrib import admin
from .models import MessageTemplate, Product, BotResponse, BotMessageHistory, BotSession

admin.site.register(MessageTemplate)
admin.site.register(Product)
admin.site.register(BotResponse)
admin.site.register(BotMessageHistory)
admin.site.register(BotSession)
