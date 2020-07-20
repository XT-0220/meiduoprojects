from django.urls import re_path, path
from . import views

urlpatterns = [

    re_path(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$',views.UsernameCountView.as_view()),

    re_path(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$',views.MobileCountView.as_view()),

    # 用户注册:POST http://www.meiduo.site:8000/register/
    path('register/', views.RegisterView.as_view()),

    path('browse_histories/',views.UserBrowseHistory.as_view()),

]