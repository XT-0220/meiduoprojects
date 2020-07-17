import random

from django import http
from django.http import HttpResponse
from django.shortcuts import render
# Create your views here.
from django.views import View
from django_redis import get_redis_connection
from apps.verifications.libs.captcha.captcha import captcha
from apps.users.views import logger
from apps.verifications.libs import captcha


class ImageCodeView(View):
    '''返回图形验证码的类视图'''
    def get(self,request,uuid):
        '''
        生成图形验证码, 保存到redis中, 另外返回图片
        :param request:
        :param uuid:
        :return:
        '''
        # 1.调用工具类 captcha 生成图形验证码
        text,image = captcha.generate_captcha()
        # 2.链接 redis, 获取链接对象
        redis_conn = get_redis_connection('verify_code')
        # 3.利用链接对象, 保存数据到 redis, 使用 setex 函数
        redis_conn.setex('img_%s' % uuid, 300, text)
        # 4.返回(图片)
        return HttpResponse(image, content_type='image/jpg')



class SMSCodeView(View):

    def get(self,request,mobile):

        # 3.创建连接到redis的对象  放到最开始
        redis_conn = get_redis_connection('verify_code')

        # 进入函数后，先获取存储在redis中的数据
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        # 查看数据是否存在，如果存在，说明60秒没到，返回
        if send_flag:
            return http.JsonResponse({'code':400,'errmsg':'发送短信过于频繁'})

        # 如果过了，在执行下面的代码

        #1.接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2.校验参数
        if not all([uuid,image_code_client]):
            return http.JsonResponse({'code':400 ,'errmsg':'缺少必传参数'} )

        # 4.提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return http.JsonResponse({'code':400 , 'errmag':'图形验证码失效'})

        # 5.删除图形验证码，避免恶意测试图形验证码
        try:
            redis_conn.delete('img_%s' %uuid)
        except Exception as e:
            logger.error(e)

        # 6.对比图形验证码
        # bytes转字符串
        image_code_server = image_code_server.decode()
        # 转小写后比较
        if image_code_client.lower( ) != image_code_server.lower():
            return http.JsonResponse({'code':400 , 'errmsg':'输入图像验证码有误'})

        # 7.生成短信验证码，生成6位数验证码
        sms_code = '%06d' % random.randint(0,999999)
        logger.info(sms_code)

        # 创建管道对象
        pl = redis_conn.pipeline()
        # redis_conn.setex('sms_%s ' %mobile,300,sms_code)
        pl.setex('sms_%s' % mobile, 300, sms_code)

        pl.setex('sms_flag_%s' % mobile,60,1)

        # 执行管道
        pl.execute()

        # 8.保存短信验证码
        # 短信验证码有效期，单位：300秒
        # redis_conn.setex('sms_%s' % mobile,300,sms_code)

        # 往redis中写入一个数据，写入什么不重要，时间重要
        # 我们给写入的数据设置为60秒，如果过期，则会获取不到
        # redis_conn.setex('send_flag_%s' % mobile , 60 , 1)

        # 9.发送短信验证码
        # 短信模板
        # CCP().send_template_sms(mobile, [sms_code, 5], 1)


        # 改为现在的写法, 注意: 这里的函数,调用的时候需要加: .delay()
        ccp_send_sms_code.delay(mobile, sms_code)


        # 10.响应结果

        return http.JsonResponse({'code':0,'errmsg':'发送短信成功'})