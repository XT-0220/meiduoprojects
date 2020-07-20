from django import http
from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.shortcuts import render
# Create your views here.
from django.views import View
from haystack.views import SearchView
from apps.contents.models import GoodsCategory
from apps.goods.models import SKU
from apps.goods.utils import get_breadcrumb


class ListView(View):
    """商品列表页
    GET /list/(?P<category_id>\d+)/skus/
    """


    def get(self, request, category_id):
        """
        提供商品列表数据和面包屑导航数据
        :param category_id: 商品第三级分类
        :return: JSON
        """
        # 接收参数
        page_num = request.GET.get('page') # 当前用户想看的页码
        page_size = request.GET.get('page_size') # 该页中想看的记录的个数
        ordering = request.GET.get('ordering') # 排序字段


        # 校验参数
        # 校验category_id是否存在
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.JsonResponse({'code': 400, 'errmsg': 'category_id不存在'})
        # 提示：page_num，page_size，ordering不需要单独校验的，因为在排序和分页时，校验的


        # 实现核心逻辑：排序和分页、面包屑导航
        # 我们查询指定分类下，未被下架的SKU信息，再排序
        skus = SKU.objects.filter(category=category, is_launched=True).order_by(ordering)


        # 分页查询
        # 创建分页器对象：分页器对象 = Paginator(要分页的查询集, 每页记录个数)
        paginator = Paginator(skus, page_size)


        # 获取指定页中的模型数据：paginator.page(页码)
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.JsonResponse({'code': 400, 'errmsg': '页码错误'})
        # 获取分页后的总页数
        total_pages = paginator.num_pages


        # 将分页后的查询集转字典列表
        list = []
        for sku in page_skus:
            list.append({
                "id": sku.id,
                "default_image_url": sku.default_image.url,
                "name": sku.name,
                "price": sku.price
            })


        # 面包屑导航
        breadcrumb = get_breadcrumb(category)


        # 响应结果
        return http.JsonResponse({
            'code': 0,
            'errmsg': 'OK',
            'breadcrumb': breadcrumb, # 面包屑导航
            'list': list, # 排序后的分页数据，不能是模型数据，因为JsonResponse不识别
            'count': total_pages # 分页后的总页数
        })

class HotGoodsView(View):

    def get(self, request, category_id):

        # 校验category_id参数是否存在
        try:
            category = GoodsCategory.objects.get(id = category_id)
        except GoodsCategory.DoesNotExist:
            return http.JsonResponse({'code': 400, 'errmsg': '参数category_id不存在'})

        # 查询指定分类下，未被下架的销量最好的前两款商品
        skus = SKU.objects.filter(category = category , is_launched = True).order_by('-sales')[:2]

        # 将查询集转字典列表
        hot_skus = []
        for sku in skus:
            hot_skus.append({
                'id':sku.id,
                'default_image_url':sku.default_image.url,
                'name':sku.name,
                'price':sku.price
            })
        return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'hot_skus': hot_skus})


class MySearchView(SearchView):
    """自定义商品搜索视图
     目的：为了重写create_response(),并返回检索后的JSON数据
     GET /search/
     """
    def create_response(self):
        """返回检索后的JSON数据"""
        # 获取检索到的数据
        context = self.get_context()

        # 获取检索到的模型数据
        results = context['page'].object_list

        # 遍历result,取出检索到的SKU，再转字典
        data_list = []
        for result in results:
            data_list.append({
                'id':result.object.id,
                'name':result.object.name,
                'price':result.object.price,
                'default_image_url':result.object.default_image.url,
                'searchkey':context.get('query'),
                'page_size':context['page'].paginator.num_pages, # 分页后的总页数
                'count':context['page'].paginator.count
            })

        # 将检索到数据转成JSON返回即可
        return http.JsonResponse(data_list, safe=False)