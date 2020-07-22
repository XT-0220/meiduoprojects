from django.urls import path, re_path

from . import views


urlpatterns = [
    # 图形验证码:GET http://www.meiduo.site:8000/image_codes/550e8400-e29b-41d4-a716-446655440000/
    # path('image_codes/<路由转换器uuid:变量名uuid>/ ', views.ImageCodeView.as_view()),
    # path('image_codes/<uuid:uuid>/', views.ImageCodeView.as_view()),
    re_path(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view()),


    # 短信验证码：GET http://www.meiduo.site:8000/sms_codes/(?P<mobile>1[3-9]\d{9})/
    # path('sms_codes/<mobile:mobile>/', views.SMSCodeView.as_view()),
    re_path(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),

]