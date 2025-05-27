# bot/serializers.py

from rest_framework import serializers
from .models import BotResponse, BotMessageHistory, Product

class BotResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BotResponse
        fields = ['id', 'intent', 'response', 'question', 'is_question']

class BotMessageHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BotMessageHistory
        fields = ['id', 'client_number', 'client_message', 'bot_response', 'timestamp']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'image',
            'price',
            'product_code',
            'is_available',
            'tags',
        ]

    def create(self, validated_data):
        # L'utilisateur connecté est automatiquement affecté
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)