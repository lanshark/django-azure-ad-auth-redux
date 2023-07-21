from django.urls import path

from .views import auth, complete


urlpatterns = [
    path("login/", auth, name="azure_login"),
    path("complete/", complete, name="azure_complete"),
]
