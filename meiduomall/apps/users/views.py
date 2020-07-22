import json,re,logging
from django import http
from django.contrib.auth import login, logout, authenticate
from django_redis import get_redis_connection
from apps.goods.models import SKU
from celery_tasks.email.tasks import send_email_verify_url
from meiduomall.utils.views import LoginRequiredJSONMixin
from apps.users.models import User,Address
from apps.users.utils import generate_email_verify_url, check_email_verify_url
from django.shortcuts import render
# Create your views here.
from django.views import View
# 日志输出器
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


class UserBrowseHistory(LoginRequiredJSONMixin,View):

    def post(self,request):
        """保存用户浏览记录"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')


        # 校验参数
        try:
            SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': 400, 'errmsg': '参数sku_id错误'})


        # 实现核心逻辑
        # 操作redis的4号库，保存sku_id作为浏览记录
        user_id = request.user.id
        # 创建连接到redis4号库的对象
        redis_conn = get_redis_connection('history')

        pl = redis_conn.pipeline()

        # 先去重
        pl.lrem('history_%s' % user_id , 0 , sku_id)
        # 再添加
        pl.lpush('history_%s' % user_id,sku_id)
        # 最后截取 ， 截取前5个（0,4）
        pl.ltrim('history_%s' % user_id,0,4)

        pl.execute()

        # 响应结果
        return http.JsonResponse({'code': 0, 'errmsg': 'OK'})



    def get(self,request):

        # 创建redis的连接对象
        redis_conn = get_redis_connection('history')
        # 使用redis操作list取出所有的sku_id
        sku_ids = redis_conn.lrange('history_%s'%request.user.id , 0 , -1)

        # 使用sku_id获取sku对象
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id = sku_id)

            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'price':sku.price
            })

        # 返回响应
        return http.JsonResponse({'code':0,'errmsg':'ok','skus':sku_list})


class AddressView(LoginRequiredJSONMixin, View):
    """获取收货地址
    GET /addresses/
    """

    def get(self, request):
        """查询收货地址"""
        # 核心逻辑：查询当前登录用户未被逻辑删除的地址
        address_model_list = request.user.addresses.filter(is_deleted=False)

        # 将地址模型列表转字典列表
        address_dict_list = []
        for address in address_model_list:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }
            address_dict_list.append(address_dict)

        # 查询当前登录用户默认地址的ID
        default_address_id = request.user.default_address_id

        return http.JsonResponse({
            "code":0,
            "errmsg":"ok",
            "default_address_id":default_address_id,
            "addresses":address_dict_list
        })


class CreateAddressView(LoginRequiredJSONMixin, View):
    """新增地址
    POST /addresses/create/
    """

    def post(self, request):
        """实现新增地址的逻辑"""
        # 补充逻辑：在每次新增地址前，我们都要判断当前登录用户未被逻辑删除的地址数量是否超过了地址上限20
        # 核心：查询出当前登录用户未被逻辑删除的地址数量
        count = request.user.addresses.filter(is_deleted=False).count()
        # 判断是否超过上限
        if count >= 20:
            return http.JsonResponse({'code': 400, 'errmsg': '地址数量超过上限'})

        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel') # 非必传
        email = json_dict.get('email') # 非必传

        # 校验参数
        # 说明：
            # province_id,city_id,district_id在这里不需要校验
            # 这里的校验仅仅是校验数据格式是否满足要求，省市区的参数传过来的是外键，外键自带约束和校验
            # 如果外键错误，在赋值的时候会自动的抛出异常，我们在赋值时可以补获异常校验
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400, 'errmsg': '参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.JsonResponse({'code': 400, 'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.JsonResponse({'code': 400, 'errmsg': '参数email有误'})

        # province = Area.objects.get(id=province_id)

        # 实现核心逻辑：将用户填写的地址数据保存到地址数据表
        # 提示：外键赋值的两种形式：
            # id对应id：user_id = request.user.id
            # 属性对应对象：user = request.user
        try:
            address = Address.objects.create(
                # user_id = request.user.id,
                user = request.user,
                # province = province,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                title = receiver, # 默认地址的标题就是收件人
                receiver = receiver,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )

            # 补充逻辑：在新增地址时，给用户绑定一个默认地址，这样做是为了保证，用户一创建了地址就会有默认地址
            # 判断当前用户是否已有默认地址
            if not request.user.default_address:
                # 如果没有默认地址，就把当前的地址作为该用户的默认地址
                request.user.default_address = address
                # request.user.default_address_id = address.id
                request.user.save()

        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '新增地址失败'})

        # 响应结果：为了让新增地址成功后，页面可以及时展示新增的地址，我们会将新增的地址响应给前端渲染
        # 构造要响应的数据
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'address': address_dict})


class EmailActiveView(View):
    """验证激活邮箱
    PUT /emails/verification/
    """

    def put(self, request):
        """实现验证激活邮箱的逻辑"""
        # 接收参数
        token = request.GET.get('token')

        # 校验参数
        if not token:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少token'})

        # 实现核心逻辑
        # 通过token提取要验证邮箱的用户
        user = check_email_verify_url(token=token)

        # 将要验证邮箱的用户的email_active字段设置True
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '邮箱验证失败'})

        # 响应结果
        return http.JsonResponse({'code': 0, 'errmsg': '邮箱验证成功'})


class EmailView(LoginRequiredJSONMixin, View):
    """添加邮箱
    PUT /emails/
    """

    def put(self, request):
        """实现添加邮箱的逻辑"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        email = json_dict.get('email')

        # 校验参数
        if not email:
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # 校验邮箱格式
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.JsonResponse({'code': 400, 'errmsg': '参数email格式错误'})

        # 实现核心逻辑：添加邮箱就是将用户填写的邮箱地址保存到当前登录用户的email字段即可
        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': 400, 'errmsg': '添加邮箱失败'})

        # 发送邮箱的验证激活邮件：耗时操作，不能让他阻塞主逻辑，需要从主逻辑中解耦出来，celery
        verify_url = generate_email_verify_url(user=request.user)
        send_email_verify_url.delay(email, verify_url)

        # 响应结果
        return http.JsonResponse({'code': 0, 'errmsg': 'OK'})


class UserInfoView(LoginRequiredJSONMixin, View):
    """用户中心
    GET /info/
    """

    def get(self, request):
        """实现用户基本信息展示
        由于我们在该接口中，判断了用户是否是登录用户
        所以能够进入到该接口的请求，一定是登录用户发送的
        所以request.user里面获取的用户信息一定是当前登录的用户信息
        如果不理解查看AuthenticationMiddleware的源代码，里面都封装好的逻辑
            Django帮助我们拿着session中提取的user_id，去数据库查询出来user，并赋值给request.user属性
        重要的技巧：
            如果该接口只有登录用户可以访问，那么在接口内部可以直接使用request.user获取到当前登录用户信息
        """
        data_dict = {
            'code': 0,
            'errmsg': 'OK',
            'info_data': {
                'username': request.user.username,
                'mobile': request.user.mobile,
                'email': request.user.email,
                'email_active': request.user.email_active
            }
        }
        return http.JsonResponse(data_dict)



class LogoutView(View):
    """退出登录
    DELETE /logout/
    """

    def delete(self, request):
        """实现退出登录的逻辑
        提示:
            退出登录的逻辑正好跟登录相反的
            如果登录成功后，记住登录状态，那么退出登录就是清理登录状态
            如果登录成功后，将用户名写入到cookie，那么退出登录就需要清理用户名cookie
        """
        # 清理登录状态
        logout(request)

        # 清理用户名cookie
        response = http.JsonResponse({'code': 0, 'errmsg': '退出登录成功'})
        response.delete_cookie('username')

        return response


class LoginView(View):
    """用户登录
    GET /login/
    """

    def post(self, request):
        """实现用户登录逻辑"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        # 该参数既可以是用户名，也可以是手机号
        account = json_dict.get('username')
        password = json_dict.get('password')
        # True、False == 可真可假，爱传不传
        remembered = json_dict.get('remembered')

        # 校验参数
        if not all([account, password]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        # if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', account):
        #     return http.JsonResponse({'code': 400, 'errmsg': '参数username格式错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return http.JsonResponse({'code': 400, 'errmsg': '参数password格式错误'})

        # 实现多账号登录
        # 判断用户输入的账号是用户名还是手机号
        if re.match(r'^1[3-9]\d{9}$', account):
            # 用户输入的账号是手机号:将USERNAME_FIELD指定为'mobile'字段
            User.USERNAME_FIELD = 'mobile'
        else:
            # 用户输入的账号是用户名:将USERNAME_FIELD指定为'username'字段
            User.USERNAME_FIELD = 'username'

        # 认证登录用户核心思想：先使用用户名作为条件去用户表查询该记录是否存在，如果该用户名对应的记录存在，再去校验密码是否正确
        # 认证登录用户：Django的用户认证系统默认已经封装好了这个逻辑
        # 认证登录用户：仅仅是为了证明当前的用户是美多商城之前的注册用户，而且密码没错
        user = authenticate(request=request, username=account, password=password)
        # 判断用户认证是否成功
        if not user:
            return http.JsonResponse({'code': 400, 'errmsg': '用户名或密码错误'})

        # 实现状态保持
        login(request, user)
        # 还需要根据remembered参数去设置状态保持的周期
        # 如果用户选择了记住登录，那么状态保持周期为两周。反之，浏览器会话结束状态保持就销毁
        if remembered:
            # 记住登录：状态保持周期为两周（就是去设置session数据的过期时间）
            # set_expiry(None)：Django封装好的，默认两周
            request.session.set_expiry(None)
            # request.session.set_expiry(14*24*3600)
        else:
            # 没有记住登录：浏览器会话结束状态保持就销毁
            request.session.set_expiry(0)

        # 在登录成功后，将用户名写入到cookie，将来会在页面右上角展示
        response = http.JsonResponse({'code': 0, 'errmsg': '登录成功'})
        response.set_cookie('username', user.username, max_age=3600*24*14)

        

        # 响应结果
        return response









