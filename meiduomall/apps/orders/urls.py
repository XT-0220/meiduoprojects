from django.urls import re_path, path
from . import views

urlpatterns = [
    re_path(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    re_path(r'^orders/commit/$', views.OrdersCommitView.as_view()),
]