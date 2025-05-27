from django.db import models
from django.conf import settings
from .nlp_utils import extract_keywords  # ✅ nécessaire

class MessageTemplate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    content = models.TextField(help_text="Contenu du message à envoyer")
    auto_trigger = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["auto_trigger"])]

    def __str__(self):
        return f"{self.title} - {self.user.company_name}"


class Product(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    product_code = models.CharField(max_length=50, blank=True, null=True, unique=True)
    is_available = models.BooleanField(default=True)
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Mots-clés liés au produit, séparés par des virgules"
    )

    def save(self, *args, **kwargs):
        if not self.tags and self.description:
            keywords = extract_keywords(self.description)
            self.tags = ",".join(keywords)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.user.company_name})"


class BotResponse(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    intent = models.CharField(max_length=100)
    question = models.CharField(max_length=255, blank=True)
    response = models.TextField()
    is_question = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.intent} → {self.response[:30]}..."


class BotMessageHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_number = models.CharField(max_length=20)
    client_message = models.TextField()
    bot_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    detected_intent = models.CharField(max_length=100, blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{self.client_number} - {self.timestamp.strftime('%d/%m %H:%M')}"

    class Meta:
        indexes = [
            models.Index(fields=["client_number"]),
            models.Index(fields=["timestamp"]),
        ]


class BotSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    client_number = models.CharField(max_length=20)
    current_intent = models.CharField(max_length=100, blank=True, null=True)
    last_question = models.TextField(blank=True, null=True)
    bot_actif = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session [{self.client_number}] - {'Actif' if self.bot_actif else 'Manuel'}"

    class Meta:
        indexes = [
            models.Index(fields=["client_number"]),
            models.Index(fields=["last_updated"]),
        ]
