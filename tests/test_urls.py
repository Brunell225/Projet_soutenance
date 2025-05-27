from django.urls import resolve
from django.views.generic import TemplateView
from rest_framework.schemas import get_schema_view
from django.contrib import admin

def test_admin_url():
    resolver = resolve("/admin/")
    assert resolver.url_name == "index", "L'URL /admin/ doit pointer vers l'admin"

def test_accounts_url_includes():
    resolver = resolve("/api/accounts/register/")
    assert resolver.url_name == "register", "L'URL /api/accounts/register/ doit être définie"

def test_bot_url_includes():
    resolver = resolve("/api/bot/send-message/")
    assert resolver.url_name == "send_whatsapp_message", "L'URL /api/bot/send-message/ doit être définie"

def test_schema_url():
    resolver = resolve("/schema/")
    assert hasattr(resolver.func.view_class, 'get'), "L'URL /schema/ doit utiliser get_schema_view"

def test_docs_url():
    resolver = resolve("/docs/")
    assert issubclass(resolver.func.view_class, TemplateView), "L'URL /docs/ doit utiliser TemplateView"
