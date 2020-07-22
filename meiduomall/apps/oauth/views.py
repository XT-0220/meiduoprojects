import json ,re
from QQLoginTool.QQtool import OAuthQQ
from django import http
from django.conf import settings
from django.contrib.auth import login
from apps.users.models import User
from django.views import View
from django_redis import get_redis_connection
from apps.oauth.models import OAuthQQUser
from apps.oauth.utils import check_access_token_openid, generate_access_token_openid
from apps.users.views import logger


class QQURLView(View):
    '''提供QQ登录页面网址'''
    def get(self,request):
        # next 表示从哪个页面进入到的登录页面
        # 将来登录成功后，就自动回到那个页面
        next = request.GET.get('next')
        # 获取 QQ 登录页面网址
        # 创建 OAuthQQ 类的对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        # 调用对象的获取 qq 地址方法
        login_url = oauth.get_qq_url()

        # 返回登录地址
        return http.JsonResponse({'code':0 , 'errmsg': 'ok','login_url':login_url})

class QQUserView(View):
    """用户扫码登录的回调处理"""
    def get(self,request):
        """Oauth2.0认证"""
        # 获取前端发送过来的 code 参数:
        code =request.GET.get('code')

        if not code:
            # 判断 code 参数是否存在
            return http.JsonResponse({'code':400 , 'errmsg':'缺少code参数'})
            # 调用我们安装的 QQLoginTool 工具类
            # 创建工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        try:
            # 携带 code 向 QQ服务器 请求 access_token
            access_token = oauth.get_access_token(code)
            # 携带 access_token 向 QQ服务器 请求 openid
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            # 如果上面获取 openid 出错, 则验证失败
            logger.error(e)
            # 返回结果
            return http.JsonResponse({'code': 400, 'errmsg': 'oauth2.0失败'})

        try:
            # 查看是否有 openid 对应的用户
            oauth_qq = OAuthQQUser.objects.get(openid = openid)

        except OAuthQQUser.DoesNotExist:
            # 如果 openid 没绑定美多商城用户
            # 请查看:  openid 未绑定用户的处理
            access_token_openid = generate_access_token_openid(openid)
            return http.JsonResponse({'code':300,'errmsg':'openid 没绑定美多商城用户','access_token':access_token_openid})

        else:
            # 如果 openid 已绑定美多商城用户
            # 根据 user 外键, 获取对应的 QQ 用户(user)
            user = oauth_qq.user
            # 实现状态保持
            login(request,user)
            # 创建重定向到主页的对象
            response = http.JsonResponse({'code':0 , 'errmsg':'ok'})
            # 将用户信息写入到 cookie 中，有效期14天
            response.set_cookie('username',user.username,max_age=3600*24*14)
            # 返回响应

            return response


    def post(self,request):
        """美多商城用户绑定到openid"""

        # 1.接收参数
        json_dict = json.loads(request.body.decode())
        mobile = json_dict.get('mobile')
        password = json_dict.get('password')
        sms_code_client = json_dict.get('sms_code')
        access_token = json_dict.get('access_token')

        # 2.校验参数
        # 判断参数是否齐全
        # if not all([mobile,password,sms_code_client,access_token]):
        #     return http.JsonResponse({'code':400, 'errmsg':'缺少必传参数'})

        if not all([mobile, password, sms_code_client, access_token]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        # 判断手机号是否合法
        if not re.match(r'^1[3-9]\d{9}$',mobile):
            return http.JsonResponse({'code': 400, 'errmsg':'请输入正确的手机号码'})

        # 判断密码是否合格
        if not re.match(r'^[0-9a-zA-Z]{8,20}$',password):
            return http.JsonResponse({'code': 400, 'errmsg': '请输入8-20位的密码'})

        # 3.判断短信验证码是否一致
        # 创建 redis 链接对象:
        redis_conn = get_redis_connection('verify_code')
        # 从 redis 中获取 sms_code 值:
        sms_code_server = redis_conn.get('sms_%s' % mobile)

        # 判断获取出来的有没有:
        if not sms_code_server:
            # 如果没有, 直接返回:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码失效'})

        # 如果有, 则进行判断:
        if sms_code_client != sms_code_server.decode():
            # 如果不匹配, 则直接返回:
            return http.JsonResponse({'code': 400, 'errmsg': '短信验证码有误'})

        # 校验openid
        openid = check_access_token_openid(access_token)
        if not openid:
            return http.JsonResponse({'code': 400, 'errmsg': '参数openid有误'})

        # 判断手机号对应的手机号是否存在
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile,password=password,mobile=mobile)
        else:
            if not user.check_password(password):
                return http.JsonResponse({'code': 400, 'errmsg': '密码有误'})


        try:
            OAuthQQUser.objects.create(user=user,openid=openid)
        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': 'QQ登录失败'})

        # 实现状态保持
        login(request=request, user=user)
        response = http.JsonResponse({'code': 0, 'errmsg': 'OK'})
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)

        # 响应结果
        return response
