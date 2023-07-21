from .views import auth, complete
from django.urls import path


urlpatterns = [
    path("login/", auth, name="azure_login"),
    path("complete/", complete, name="azure_complete"),
]
