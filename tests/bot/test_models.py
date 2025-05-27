import pytest
from bot.models import BotResponse

@pytest.mark.django_db
def test_bot_response_str(create_authenticated_user):
    user, _ = create_authenticated_user
    response = BotResponse.objects.create(
        user=user,
        intent="salutation",
        response="Bonjour, comment puis-je vous aider ?"
    )
    assert str(response) == "salutation"
