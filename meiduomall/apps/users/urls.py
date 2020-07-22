from django.urls import re_path, path
from . import views

urlpatterns = [

    # 判断用户名是否重复注册:GET /usernames/itcast/count/
    # path('usernames/itcast/count/', views.UsernameCountView.as_view()),
    # path('usernames/<'匹配用户名的路由转换器:变量'>/count/', views.UsernameCountView.as_view()),
    re_path(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$' , views.UsernameCountView.as_view()),

    # 判断手机号是否重复注册:GET http://www.meiduo.site:8000/mobiles/18500001111/count/
    re_path(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # 用户注册:POST http://www.meiduo.site:8000/register/
    path('register/', views.RegisterView.as_view()),

    # 用户登录:GET http://www.meiduo.site:8000/login/
    path('login/', views.LoginView.as_view()),

    # 退出登录：DELETE http://www.meiduo.site:8000/logout/
    path('logout/', views.LogoutView.as_view()),

    # 用户中心：GET http://www.meiduo.site:8000/info/
    path('info/', views.UserInfoView.as_view()),

    # 添加邮箱:PUT http://www.meiduo.site:8000/emails/
    path('emails/', views.EmailView.as_view()),

    # 验证激活邮箱:PUT http://www.meiduo.site:8000/emails/verification/
    path('emails/verification/', views.EmailActiveView.as_view()),

    # 新增地址:POST http://www.meiduo.site:8000/addresses/create/
    path('addresses/create/', views.CreateAddressView.as_view()),

    # 获取收货地址:GET http://www.meiduo.site:8000/addresses/
    path('addresses/', views.AddressView.as_view()),

    # 用户浏览记录：POST /browse_histories/
    path('browse_histories/', views.UserBrowseHistory.as_view()),

]