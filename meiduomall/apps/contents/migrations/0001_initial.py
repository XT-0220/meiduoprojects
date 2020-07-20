# Generated by Django 2.2.5 on 2020-07-19 12:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ContentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=50, verbose_name='名称')),
                ('key', models.CharField(max_length=50, verbose_name='类别键名')),
            ],
            options={
                'db_table': 'tb_content_category',
            },
        ),
        migrations.CreateModel(
            name='GoodsCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=10, verbose_name='名称')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subs', to='contents.GoodsCategory', verbose_name='父类别')),
            ],
            options={
                'db_table': 'tb_goods_category',
            },
        ),
        migrations.CreateModel(
            name='GoodsChannelGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('name', models.CharField(max_length=20, verbose_name='频道组名')),
            ],
            options={
                'db_table': 'tb_channel_group',
            },
        ),
        migrations.CreateModel(
            name='GoodsChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('url', models.CharField(max_length=50, verbose_name='频道页面链接')),
                ('sequence', models.IntegerField(verbose_name='组内顺序')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contents.GoodsCategory', verbose_name='顶级商品类别')),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contents.GoodsChannelGroup', verbose_name='频道组名')),
            ],
            options={
                'db_table': 'tb_goods_channel',
            },
        ),
        migrations.CreateModel(
            name='Content',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('title', models.CharField(max_length=100, verbose_name='标题')),
                ('url', models.CharField(max_length=300, verbose_name='内容链接')),
                ('image', models.ImageField(blank=True, null=True, upload_to='', verbose_name='图片')),
                ('text', models.TextField(blank=True, null=True, verbose_name='内容')),
                ('sequence', models.IntegerField(verbose_name='排序')),
                ('status', models.BooleanField(default=True, verbose_name='是否展示')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='contents.ContentCategory', verbose_name='类别')),
            ],
            options={
                'db_table': 'tb_content',
            },
        ),
    ]
