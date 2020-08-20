import json,pickle,base64
from django import http
from django.conf.locale import pl
from django.shortcuts import render
# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from apps.goods.models import SKU


class CartsView(View):
    """购物车管理：增删改查
    增：POST /carts/
    查：GET /carts/
    改：PUT /carts/
    删：DELETE /carts/
    """

    def post(self,request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')

        selected = json_dict.get('selected',True)

        # 校验参数
        if not all([sku_id,count]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        try:
            SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': 400, 'errmsg': '参数sku_id错误'})

        try:
            count = int(count)
        except Exception:
            return http.JsonResponse({'code': 400, 'errmsg': '参数count错误'})

        # 校验selected类型
        if not isinstance(selected,bool):
            return http.JsonResponse({'code': 400, 'errmsg': '参数selected错误'})

        # 核心逻辑
        if request.user.is_authenticated:
            # 如果用户已登录，新增redis购物车
            # 创建连接到redis5号库的对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            user_id = request.user.id
            pl.hincrby('carts_%s' %user_id,sku_id,count)
            if selected:
                pl.sadd('selected_%s'%user_id,sku_id)
            pl.execute()

            return http.JsonResponse({'code': 0, 'errmsg': 'OK'})
        else:
            # 如果用户未登录，新增cookie购物车
            # 1.从cookie中读取购物车字典
            # 从cookie中读取之前保存的购物车密文字符串
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_str_bytes = cart_str.encode()
                cart_dict_bytes = base64.b64decode(cart_str_bytes)
                cart_dict = pickle.loads(cart_dict_bytes)
            else:
                cart_dict = {}
            # 添加购物车到数据到购物车字典
            if sku_id in cart_dict:
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            # 3.购物车字典转字符串并写入到cookie
            # 先使用pickle将cart_dict序列化为bytes类型的字典

            cart_dict_bytes = pickle.dumps(cart_dict)
            # 在使用base64将bytes类型的字典编码为bytes类型的密文字符串
            cart_str_bytes = base64.b64decode(cart_dict_bytes)
            # 然后再将bytes类型的密文字符串转正真的字符串
            cookie_cart_str = cart_str_bytes.decode()

            # 最后将密文字符串写入到cookie
            response = http.JsonResponse({'code': 0, 'errmsg': 'OK'})
            response.set_cookie('carts', cookie_cart_str)
            return response


    def get(self,request):

        # 判断用户是否登录
        if request.user.is_authenticated:
            # 如果用户已登录，查询redis购物车
            user_id = request.user.id
            redis_conn = get_redis_connection('carts')
            redis_cart = redis_conn.hgetall('carts_%s'%user_id)
            redis_selected = redis_conn.smembers('selected_%s'%user_id)

            cart_dict = {}
            for sku_id ,count in redis_cart.items():
                cart_dict[int(sku_id)] = {
                    'count':int(count),
                    'selected':sku_id in redis_selected,
                }
        else:
            # 如果用户未登录，查询cookie购物车
            # 从cookie中读取购物车字典
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}

        # 读取购物车里面的商品信息
        sku_ids = cart_dict.keys()
        sku_model_list = SKU.objects.filter(id__in = sku_ids)

        cart_skus = []
        for sku in sku_model_list:
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price,
                'count': cart_dict[sku.id]['count'],
                'selected': cart_dict[sku.id]['selected'],
                'amount': sku.price * cart_dict[sku.id]['count']
            })

        # 响应结果
        return http.JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})


    def put(self,request):

        #接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')
        #校验参数
        if not all([sku_id,count,selected]):
            return http.JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})

        try:
            SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': 400, 'errmsg': '参数sku_id错误'})
        try:
            count = int(count)
        except Exception:
            return http.JsonResponse({'code': 400, 'errmsg': '参数count错误'})
        # 校验selected类型
        if not isinstance(selected,bool):
            return http.JsonResponse({'code': 400, 'errmsg': '参数selected错误'})

        #核心逻辑 判断用户是否登录
        if request.user.is_authenticated:
            user_id = request.user.id
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hset('carts_%s'%user_id,sku_id,count)
            if selected:
                pl.sadd('selected_%s'%user_id,sku_id)
            else:
                pl.srem('selected_%s'%user_id,sku_id)
            pl.execute()

            # 在修改成功后，记得将修改后的数据返回给前端，实现局部刷新的效果
            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected
            }
            return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_sku': cart_sku})
        else:
            # 如果用户未登录，修改cookie购物车
            # 由于前端向后端发送的是修改后的数据，所以后端直接覆盖写入即可
            # 从cookie中读取购物车字典
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
                # 修改购物车字典
            cart_dict[sku_id] = {
                'count':count,
                'selected':selected
            }
            # 将购物车字典转字符串并写入到cookie
            cookie_cart_str = base64.b64decode(cart_dict).decode()
            # 构造响应数据
            cart_sku = {
                'id':sku_id,
                'count':count,
                'selected':selected
            }
            response = http.JsonResponse({'code': 0, 'errmsg': 'OK', 'cart_sku': cart_sku})
            response.set_cookie('carts', cookie_cart_str)
            return response


    def delete(self,request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 校验参数
        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.JsonResponse({'code': 400, 'errmsg': 'error'})

        # 核心逻辑  判断用户是否登录
        if request.user.is_authenticated:
            # 如果用户已登录，删除redis购物车
            user_id = request.user.id
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            pl.hdel('carts_%s'%user_id,sku_id)
            pl.srem('selected_%s'%user_id,sku_id)
            pl.execute()
            return http.JsonResponse({'code': 0, 'errmsg': 'OK'})
        else:
            # 如果用户未登录，删除cookie购物车
            # 从cookie中读取购物车字典
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.load(base64.b64decode(cart_str.encode()))
            else:
                cart_dict = {}
                # 删除购物车字典中的key
                # 注意点：在删除字典的key时，必须判断字典的key是否存在，只能删除存在的key,如果删了不存在的key,会报错
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            # 将购物车字典转字符串并写入到cookie
            cookie_cart_str = base64.b64decode(cart_dict).decode()

            response = http.JsonResponse({'code': 0, 'errmsg': 'OK'})
            response.set_cookie('carts', cookie_cart_str)
            return response


class CartSelectAllView(View):

    def put(self,request):
        # 接收参数
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected',True)
        # 校验参数
        if selected:
            if not isinstance(selected,bool):
                return http.JsonResponse({'code': 400, 'errmsg': 'selected参数错误'})

        # 判断用户是否登录
        user = request.user
        if user.is_authenticated:
            # 用户已登录
            # 创建redis对象
            redis_conn = get_redis_connection('carts')
            # 读取hash中所有的sku_id
            item_dict = redis_conn.hgetall('carts_%s'%user.id)
            # 读取字典中所有的sku_id
            sku_ids = item_dict.keys()
            # 确定全选或取消全选
            if selected:
                # 确定全选：将sku_ids中所有的sku_id添加到set
                redis_conn.sadd('selected_%s'% user.id, *sku_ids)
            else:
                # 取消全选：将sku_ids中所有的sku_id从set中移除
                redis_conn.srem('selected_%s'% user.id, *sku_ids)
            return http.JsonResponse({'code': 0, 'errmsg': 'OK'})
        else:
            # 用户未登录，操作 cookie 购物车
            # 从cookie中读取购物车字典
            cookie_cart = request.COOKIES.get('carts')
            response = http.JsonResponse({'code': 0, 'errmsg': 'OK'})
            if cookie_cart:
                cart_dict = pickle.loads(base64.b64decode(cookie_cart.encode()))
                # 将购物车字典中所有的selected字段设置为True或Flase
                for sku_id in cart_dict.keys:
                    cart_dict[sku_id]['seleccted'] = selected
                    # 将购物车字典转字符串并写入到cookie
                cart_data = base64.b64decode(pickle.dumps(cart_dict)).decode()

                response.set_cookie('carts',cart_data)
            return response

