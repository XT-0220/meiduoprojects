from django import http
from apps.users.models import User
import logging
from django.shortcuts import render
# Create your views here.
from django.views import View
logger = logging.getLogger('django')

class UsernameCountView(View):
    '''判断用户名是否注册'''
    def get(self,request,username):
        '''判断用户名是否重复'''
        # 查询username在数据库中的个数
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return http.JsonResponse({'code': 400 ,'errmsg':'访问数据库失败'})

        # 返回结果（json）
        return http.JsonResponse({'code':0 , 'errmsg':'ok','count':count})

class MobileCountView(View):

    def get(self,request,mobile):

        try:
            count = User.objects.filter(mobile = mobile).count()
        except Exception as e:
            return http.JsonResponse({'code': 400 ,'errmsg':'访问数据库失败'})

        return http.JsonResponse({'code':0,'errmsg':'ok','count':count})

