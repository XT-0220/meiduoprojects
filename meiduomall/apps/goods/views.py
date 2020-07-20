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

    def get(self, request, category_id):

        # 获取参数
        page_num = request.GET.get('page')
        page_size = request.GET.get('page_size')
        sort = request.GET.get('ordering')

        # 判断category_id 是否正确
        try:
            category = GoodsCategory.objects.get(id = category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code':400 , 'errmsg':'获取sql数据错误'})

        # 查询面包屑导航
        breadcrumb = get_breadcrumb(category)

        # 排序
        try:
            skus = SKU.objects.filter(category=category , is_launched = True).order_by(sort)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400 , 'errmsg':'获取sql数据错误'})

        paginator = Paginator(skus,5)
        # 获取每页数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return JsonResponse({'code':400 , 'errmsg':'page数据出错'})

        # 获取列表页总页数
        total_page = paginator.num_pages

        # 定义列表
        list = []
        for sku in page_skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image.url,
                'name':sku.name,
                'price':sku.price
            })
        # 把数据变为json发送给前端

        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'breadcrumb':breadcrumb,
            'list':list,
            'count':total_page
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