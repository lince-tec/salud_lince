from django.urls import path

from .views import consultar_chatbot


urlpatterns = [
    path(
        'consultar/',
        consultar_chatbot,
        name='consultar_chatbot'
    ),
]