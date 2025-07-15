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
    # ✅ Ajout des tailles et couleurs
    sizes = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False
    )
    colors = serializers.ListField(
        child=serializers.CharField(max_length=20),
        required=False
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'image',  # <-- fichier image depuis Flutter
            'price',
            'product_code',
            'is_available',
            'tags',
            'sizes',
            'colors',
            'payment_link',
            'deposit_number',
        ]

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Le nom du produit ne peut pas être vide.")
        return value

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


# ✅ Nouveau serializer pour afficher les détails complets du produit
class ProductDetailSerializer(serializers.ModelSerializer):
    image_path = serializers.SerializerMethodField()
    sizes = serializers.ListField(child=serializers.CharField(), read_only=True)
    colors = serializers.ListField(child=serializers.CharField(), read_only=True)
    formatted_price = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'image_path',          # ✅ chemin relatif du fichier image
            'formatted_price',     # ✅ prix formaté en FCFA
            'stock',
            'product_code',
            'is_available',
            'tags_list',           # ✅ liste de mots-clés
            'sizes',
            'colors',
            'payment_link',
            'deposit_number',
        ]

    def get_image_path(self, obj):
        if obj.image:
            return obj.image.url  # /media/products/image.jpg
        return None

    def get_formatted_price(self, obj):
        return f"{obj.price:,.0f} FCFA"

    def get_tags_list(self, obj):
        return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
