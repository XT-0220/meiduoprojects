# Create your views here.
from django import http
from django.core.cache import cache
from django.views import View
from apps.areas.models import Area



class ProvinceAreaView(View):
    """查询省份数据
    GET /areas/
    """
    def get(self,request):
        """实现查询省份数据的逻辑"""
        # 读取缓存:如果在逻辑最开始的时候，读取到缓存，那么后面的所有逻辑，一概不执行
        province_dict_list = cache.get('province_list')
        if province_dict_list:
            return http.JsonResponse({'code':0 ,'errmsg':'ok','province_list':province_dict_list})

        # 查询省份数据：省份数据没有父级
        # Area.objects.all() # 查询所有的省市区
        # Area.objects.get() # 只能查一个
        province_model_list = Area.objects.filter(parent=None)
        # 将查询集模型列表转字典列表
        province_dict_list = []
            # 把模型数据转成字典数据
        for province_model in province_model_list:
            province_dict_list.append({'id':province_model.id,'name':province_model.name})

        # 缓存省份字典列表
        # cache.set('key', 'value', '过期时间，单位秒')
        cache.set('province_list',province_dict_list,3600)
        # 重要提示：JsonResponse()不识别模型数据(模型对象和查询集)，他只识别字典，列表，字典列表
        return http.JsonResponse({'code':0,'errmsg':'ok','province_list':province_dict_list})




class SubAreaView(View):

    """查询城市或者区县数据
    GET /areas/(?P<pk>[1-9]\d+)/
    说明：
        对于省市区的数据，不是用户必须交互或者必须得到结果的，没有数据就可以不用管
        如果希望项目中的任何错误，都在日志中输出，那么这个时候就可以try
        但是，个人建议，开发时，遇到任何的数据库的错误，都必须try，这样做更加严谨一些
    """
    def get(self,request,parentid):
        """
        实现查询城市或者区县数据的逻辑
        :param parentid: 省份ID、城市ID
        :return: 城市数据、区县数据
        说明：如果parentid是省份ID，那么就查城市数据。如果parentid是城市ID，那么就查区县数据。
        """
        # 读取缓存
        sub_data = cache.get('sub_data_%s' % parentid)
        if sub_data:
            return http.JsonResponse({'code':0 , 'errmsg':'ok','sub_data':sub_data})
        # 查询当前的父级地区：省份或者城市
        parent_area = Area.objects.get(id = parentid)
        # 查询当前父级地区的子级（一查多）：省份查城市、城市查区县，要查询父级对应的所有子级，所以会调用all()
        sub_model_list = parent_area.subs.all()
        # 将子级的模型列表转字典列表
        subs = []
        for sub_model in sub_model_list:
            sub_dict = {'id':sub_model.id , 'name':sub_model.name}
            subs.append(sub_dict)
        # 子级数据:城市或者区县
        sub_data = {'id':parent_area.id , 'name':parent_area.name , 'subs':subs}

        # 缓存子级数据
        # 说明：
            # 对于子级的缓存，我们需要区分当前缓存的是哪个父级的子级，
            # 比如：需要区分当前缓存的是河北省的城市还是山西省的城市，如果不做区分，数据就会被覆盖
        cache.set('sub_data_%s' % parentid,sub_data,3600)

        return http.JsonResponse({"code": "0", "errmsg": "OK", "sub_data": sub_data})