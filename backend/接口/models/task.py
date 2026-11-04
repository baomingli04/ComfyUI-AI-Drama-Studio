# -*- coding: utf-8 -*-
"""task 表模型：对应 aicg.task 表，全部任务一张表、无子表。"""
from django.db import models


class task(models.Model):
    """task 表：一次生成任务的全部输入与产物。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    类型 = models.CharField(max_length=50, db_column='类型', verbose_name='类型')
    状态 = models.CharField(max_length=20, default='已创建', db_column='状态', verbose_name='状态')
    创建人id = models.ForeignKey('用户', on_delete=models.RESTRICT, db_column='创建人id', verbose_name='创建人')
    comfy_prompt_id = models.CharField(max_length=64, blank=True, null=True, db_column='comfy_prompt_id', verbose_name='ComfyUI提示词ID')
    日志路径 = models.CharField(max_length=512, blank=True, null=True, db_column='日志路径', verbose_name='日志路径')
    正向提示词 = models.TextField(blank=True, null=True, db_column='正向提示词', verbose_name='正向提示词')
    反向提示词 = models.TextField(blank=True, null=True, db_column='反向提示词', verbose_name='反向提示词')
    图片宽 = models.IntegerField(blank=True, null=True, db_column='图片宽', verbose_name='图片宽')
    图片高 = models.IntegerField(blank=True, null=True, db_column='图片高', verbose_name='图片高')
    视频宽 = models.IntegerField(blank=True, null=True, db_column='视频宽', verbose_name='视频宽')
    视频高 = models.IntegerField(blank=True, null=True, db_column='视频高', verbose_name='视频高')
    一采MP = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, db_column='一采MP', verbose_name='一采MP')
    二采MP = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, db_column='二采MP', verbose_name='二采MP')
    比例 = models.CharField(max_length=16, blank=True, null=True, db_column='比例', verbose_name='比例')
    视频时长 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, db_column='视频时长', verbose_name='视频时长')
    cfg = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True, db_column='cfg', verbose_name='cfg')
    seed = models.BigIntegerField(blank=True, null=True, db_column='seed', verbose_name='seed')
    模式 = models.CharField(max_length=16, blank=True, null=True, db_column='模式', verbose_name='模式')
    生成声音 = models.BooleanField(blank=True, null=True, db_column='生成声音', verbose_name='生成声音')
    步数 = models.IntegerField(blank=True, null=True, db_column='步数', verbose_name='步数')
    采样器 = models.CharField(max_length=50, blank=True, null=True, db_column='采样器', verbose_name='采样器')
    底膜精度 = models.CharField(max_length=8, blank=True, null=True, db_column='底膜精度',
                              verbose_name='底膜精度',
                              help_text='导演台全能用：auto=工作流默认 / bf16 / int8，决定 unet_name 具体文件')
    水印 = models.CharField(max_length=50, blank=True, null=True, db_column='水印', verbose_name='水印')
    系统提示词 = models.TextField(blank=True, null=True, db_column='系统提示词', verbose_name='系统提示词')
    组1提示词 = models.TextField(blank=True, null=True, db_column='组1提示词', verbose_name='组1提示词')
    组2提示词 = models.TextField(blank=True, null=True, db_column='组2提示词', verbose_name='组2提示词')
    组3提示词 = models.TextField(blank=True, null=True, db_column='组3提示词', verbose_name='组3提示词')
    组4提示词 = models.TextField(blank=True, null=True, db_column='组4提示词', verbose_name='组4提示词')
    组1时长 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, db_column='组1时长', verbose_name='组1时长')
    组2时长 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, db_column='组2时长', verbose_name='组2时长')
    组3时长 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, db_column='组3时长', verbose_name='组3时长')
    组4时长 = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, db_column='组4时长', verbose_name='组4时长')
    输入图1 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图1', verbose_name='输入图1')
    输入图2 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图2', verbose_name='输入图2')
    输入图3 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图3', verbose_name='输入图3')
    输入图4 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图4', verbose_name='输入图4')
    输入图5 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图5', verbose_name='输入图5')
    输入图6 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图6', verbose_name='输入图6')
    输入图7 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图7', verbose_name='输入图7')
    输入图8 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图8', verbose_name='输入图8')
    输入图9 = models.CharField(max_length=512, blank=True, null=True, db_column='输入图9', verbose_name='输入图9')
    输入视频1 = models.CharField(max_length=512, blank=True, null=True, db_column='输入视频1', verbose_name='输入视频1')
    输入视频2 = models.CharField(max_length=512, blank=True, null=True, db_column='输入视频2', verbose_name='输入视频2')
    输入视频3 = models.CharField(max_length=512, blank=True, null=True, db_column='输入视频3', verbose_name='输入视频3')
    输入音频1 = models.CharField(max_length=512, blank=True, null=True, db_column='输入音频1', verbose_name='输入音频1')
    输入音频2 = models.CharField(max_length=512, blank=True, null=True, db_column='输入音频2', verbose_name='输入音频2')
    输入音频3 = models.CharField(max_length=512, blank=True, null=True, db_column='输入音频3', verbose_name='输入音频3')
    回复 = models.TextField(blank=True, null=True, db_column='回复', verbose_name='回复')
    产物图片 = models.CharField(max_length=512, blank=True, null=True, db_column='产物图片', verbose_name='产物图片')
    产物图片2 = models.CharField(max_length=512, blank=True, null=True, db_column='产物图片2', verbose_name='产物图片2')
    产物视频1 = models.CharField(max_length=512, blank=True, null=True, db_column='产物视频1', verbose_name='产物视频1')
    产物视频2 = models.CharField(max_length=512, blank=True, null=True, db_column='产物视频2', verbose_name='产物视频2')
    错误信息 = models.TextField(blank=True, null=True, db_column='错误信息', verbose_name='错误信息')
    错误文件 = models.CharField(max_length=512, blank=True, null=True, db_column='错误文件', verbose_name='错误文件')
    错误行号 = models.IntegerField(blank=True, null=True, db_column='错误行号', verbose_name='错误行号')
    错误函数 = models.CharField(max_length=100, blank=True, null=True, db_column='错误函数', verbose_name='错误函数')
    创建时间 = models.DateTimeField(db_column='创建时间', verbose_name='创建时间')
    开始时间 = models.DateTimeField(blank=True, null=True, db_column='开始时间', verbose_name='开始时间')
    结束时间 = models.DateTimeField(blank=True, null=True, db_column='结束时间', verbose_name='结束时间')

    class Meta:
        db_table = 'task'
        verbose_name = '任务'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f'{self.id}-{self.类型}'
