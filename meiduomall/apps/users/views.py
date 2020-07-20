import json
import re

from django import http
from django.contrib.auth import login
from django_redis import get_redis_connection

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
            return http.JsonResponse({'code': 400,'errmsg':'访问数据库失败'})

        # 返回结果（json）
        return http.JsonResponse({'code':0, 'errmsg':'ok','count':count})

class MobileCountView(View):

    def get(self,request,mobile):

        try:
            count = User.objects.filter(mobile = mobile).count()
        except Exception as e:
            return http.JsonResponse({'code': 400 ,'errmsg':'访问数据库失败'})

        return http.JsonResponse({'code':0,'errmsg':'ok','count':count})

class RegisterView(View):
    """用户注册
    POST http://www.meiduo.site:8000/register/
    """

    def post(self, request):
        """实现注册逻辑"""
        # 接收参数：请求体中的JSON数据 request.body
        json_bytes = request.body # 从请求体中获取原始的JSON数据，bytes类型的
        json_str = json_bytes.decode() # 将bytes类型的JSON数据，转成JSON字符串
        json_dict = json.loads(json_str) # 将JSON字符串，转成python的标准字典
        # json_dict = json.loads(request.body.decode())

        # 提取参数
        username = json_dict.get('username')
        password = json_dict.get('password')
        password2 = json_dict.get('password2')
        mobile = json_dict.get('mobile')
        # 提取短信验证码
        sms_code_client = json_dict.get('sms_code')
        allow = json_dict.get('allow')

        # 校验参数
        # 判断是否缺少必传参数
        # all([]): 判断某些数据中是否有为空的数据
        # 只要列表中元素有任意一个为空，那么就返回False，只有所有的元素不为空，才返回True
        # all([username, password, password2, mobile, allow])
        if not all([username, password, password2, mobile, sms_code_client, allow]):
            # 如果缺少了必传参数，就返回400的状态码和错误信息，立马终止逻辑
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        # 判断用户名是否满足项目的格式要求
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            # 如果用户名不满足格式要求，返回错误信息，立马终止逻辑
            return http.JsonResponse({'code': 400, 'errmsg': '参数username有误'})
        # 判断密码是否满足项目的格式要求
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            # 如果密码不满足格式要求，返回错误信息，立马终止逻辑
            return http.JsonResponse({'code': 400, 'errmsg': '参数password有误'})
        # 判断用户两次输入的密码是否一致
        if password != password2:
            return http.JsonResponse({'code': 400, 'errmsg': '两次输入不对'})
        # 判断手机号是否满足项目的格式要求
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})

        # 判断短信验证码是否正确：跟图形验证码的验证一样的逻辑
        # 提取服务端存储的短信验证码：以前怎么存储，现在就怎么提取
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get('sms_%s' % mobile) # sms_code_server是bytes
        # 判断短信验证码是否过期
        if not sms_code_server:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码失效'})
        # 对比用户输入的和服务端存储的短信验证码是否一致
        if sms_code_client != sms_code_server.decode():
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码有误'})

        # 判断是否勾选协议
        if allow != True:
            return http.JsonResponse({'code': 400, 'errmsg': '参数allow有误'})

        # 实现核心逻辑：保存注册数据到用户数据表
        # 由于美多商城的用户模块完全依赖于Django自带的用户模型类
        # 所以用户相关的一切操作都需要调用Django自带的用户模型类提供的方法和属性
        # 其中就包括了保存用户的注册数据，Django自带的用户模型类提行了create_user()专门保存用户的注册数据
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '注册失败'})

        # 实现状态保持：因为美多商城的需求是注册成功即登录成功
        # 我们记住当前的用户登录过的，cookie机制(不选的)，session机制（OK）
        # 如何证明当前的用户登录过，选择session机制，包含了记住登录状态和校验登录的状态
        # login()方法是Django提供的用于实现登录、注册状态保持
        # login('请求对象', '注册后或者登录认证后的用户')
        login(request, user)

        # 在注册成功后，将用户名写入到cookie，将来会在页面右上角展示
        response = http.JsonResponse({'code': 0, 'errmsg': '注册成功'})
        response.set_cookie('username', user.username, max_age=3600*24*14)

        # 响应结果：如果注册成功，前端会把用户引导到首页
        return response
