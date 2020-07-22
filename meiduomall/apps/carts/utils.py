import base64,pickle
from django_redis import get_redis_connection


def merge_cart_cookie_to_redis(request, user, response):
    """合并cookie购物车到redis购物车"""
    # 从cookie中读取购物车数据
    cart_str = request.COOKIES.get('carts')
    # 如果cookie中无购物车数据，终止逻辑
    if not cart_str:
        return response

    # 如果cookie中有购物车数据，转购物车字典
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

    # 准备新的数据容器：{sku_id: count}、[selected_sku_id]、[unselected_sku_id]
    new_cart_dict = {} # 保存商品和数量
    new_add_selected = [] # 保存被勾选的商品编号
    new_remove_selected = [] # 保存未被勾选的商品编号

    """
    {
      "sku_id1":{
        "count":1,
        "selected":True
      },
      "sku_id2":{
        "count":2,
        "selected":False
      }
    }
    """
    # 遍历cookie中购物车字典，将要合并的数据添加到数据容器(重要)
    for sku_id, cart_dict in cart_dict.items():
        new_cart_dict[sku_id] = cart_dict['count']

        if cart_dict['selected']:
            new_add_selected.append(sku_id)
        else:
            new_remove_selected.append(sku_id)

    # 将数据容器中的购物车数据同步到redis数据库(重要)
    redis_conn = get_redis_connection('carts')
    pl = redis_conn.pipeline()
    pl.hmset('carts_%s'%user.id, new_cart_dict)
    if new_add_selected:
        pl.sadd('selected_%s'%user.id, *new_add_selected)
    if new_remove_selected:
        pl.srem('selected_%s'%user.id, *new_remove_selected)
    pl.execute()

    # 清空cookie中购物车数据
    response.delete_cookie('carts')

    return response