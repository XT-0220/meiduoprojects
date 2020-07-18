from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View

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
                'default_image_url':sku.default_image_url,
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