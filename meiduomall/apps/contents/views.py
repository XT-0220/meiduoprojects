from django.shortcuts import render

# Create your views here
from django.views import View

from apps.contents.models import GoodsCategory, GoodsChannel, ContentCategory


# class IndexView(View):
#
#     def get(self,request):
#
#         # 准备商品字典容器
#         categories = {}
#
#         # 查询所有频道
#         channels = GoodsChannel.objects.order_by('group_id','sequence')
#         # 遍历所有频道
#         for channel in channels:
#             group_id = channel.group.id
#             if group_id not in categories:
#                 categories[group_id] = {'channels':[],'sub_cats':[]}
#
#
#             # 获取一级分类
#             cat1 = channel.category
#             # 添加数据
#             categories[group_id]['channels'].append({
#                 'id':channel.id,
#                 'name':cat1.name,
#                 'url':channel.url
#             })
#
#             # 添加二级和三级
#             for cat2 in cat1.subs.all():
#
#                 sub_cats = []
#                 for cat3 in cat2.subs.all():
#                     sub_cats.append({
#                         'id':cat2.id,
#                         'name':cat2.name
#                     })
#
#                 categories[group_id]['sub_cats'].append({
#                     'id':cat2.id,
#                     'name':cat2.name,
#                     'sub_cats': sub_cats
#                 })
#
#         # 查询首页广告数据
#         contents = {}
#         # 先查询所有广告种类，并遍历
#         content_categories = ContentCategory.objects.all()
#         for content_cat in content_categories:
#             contents[content_cat.key] = content_cat.content_set.filter(status=True).order_by('sequence')
#
#         pass

