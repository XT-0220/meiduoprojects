from django.db import models

# Create your models here.

class Area(models.Model):
    """省市区"""
    name = models.CharField(max_length=20, verbose_name='名称')
    parent = models.ForeignKey('self', related_name='subs', null=True, on_delete=models.SET_NULL, verbose_name='上级行政地区')

    class Meta:
        db_table = 'tb_areas'

    def __str__(self):
        return self.name


"""
一对多的关联查询的套路
一方模型：BookInfo
多方模型：HeroInfo

一查多：
	一方模型对象.多方模型类名小写_set
多查一：
	多方模型对象.外键属性名

自关联的表就是将多张一对多的表的关系和数据合并到一张表
结论：
    自关联的查询也就是一查多和多查一的套路
    省查询市(一查多)：
        模型对象.模型类名小写_set
    市查询省(多查一)：
        模型对象.外键属性名

重要提示：
    默认一查多的关联字段：多方模型类名小写_set
    默认多查一的关联字段：外键属性名

自定义一查多的关联字段
    为什么要自定义一查多的关联字段？
        因为，有可能出现模型类的类名特别长的情况，那么使用默认的一查多的关联字段时，代码不够简洁
        所以，为了让一查多的语法更加简洁，我们可以选择自定义一查多的关联字段

    实现方式：
        related_name选项，专门用来自定义一查多的关联字段的
        parent = models.ForeignKey('self', related_name='自定义字段名', null=True, on_delete=models.SET_NULL)
    使用方式：
        没有自定义一查多的关联字段时：
            省查询市(一查多)：
                模型对象.模型类名小写_set
        如果自定义一查多的关联字段时：
            related_name='hehe'
            省查询市(一查多)：
                模型对象.hehe

            related_name='subs'
            省查询市(一查多)：
                模型对象.subs

    注意点：
        如果自定义一查多的关联字段，那么默认的一查多的关联字段将失效，无用。如果强制使用会报错的。
        任何一对多的关联字段都可以自定义，不仅仅是自关联。
"""