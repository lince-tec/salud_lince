from django.urls import path

from .views import (
    chatbot_view,
    consultar_chatbot
)

urlpatterns = [

    path(
        '',
        chatbot_view,
        name='chatbot'
    ),

    path(
        'consultar/',
        consultar_chatbot,
        name='consultar_chatbot'
    ),

]