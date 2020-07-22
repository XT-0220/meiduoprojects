from django.urls import re_path, path
from . import views

urlpatterns = [

    path('carts/',views.CartsView.as_view()),

    path('carts/selection/',views.CartSelectAllView.as_view()),




]