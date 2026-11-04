# -*- coding: utf-8 -*-
"""模型配置表模型：对应 aicg.模型配置 表。"""
from django.db import models


class 模型配置(models.Model):
    """模型配置表：LLM 与 ComfyUI 地址等配置，单行占位。"""

    id = models.BigAutoField(primary_key=True, db_column='id', verbose_name='主键')
    大模型名称 = models.CharField(max_length=100, blank=True, null=True, db_column='大模型名称', verbose_name='大模型名称')
    LLM地址 = models.CharField(max_length=255, blank=True, null=True, db_column='LLM地址', verbose_name='LLM地址')
    LLM密钥 = models.CharField(max_length=255, blank=True, null=True, db_column='LLM密钥', verbose_name='LLM密钥')
    LLM模型名 = models.CharField(max_length=100, blank=True, null=True, db_column='LLM模型名', verbose_name='LLM模型名')
    ComfyUI地址 = models.CharField(max_length=255, blank=True, null=True, db_column='ComfyUI地址', verbose_name='ComfyUI地址')
    ComfyUI工作流目录 = models.CharField(max_length=512, blank=True, null=True, db_column='ComfyUI工作流目录', verbose_name='ComfyUI工作流目录')
    ComfyUI输出目录 = models.CharField(max_length=512, blank=True, null=True, db_column='ComfyUI输出目录', verbose_name='ComfyUI输出目录')
    更新时间 = models.DateTimeField(db_column='更新时间', verbose_name='更新时间')

    class Meta:
        db_table = '模型配置'
        verbose_name = '模型配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.大模型名称 or ''
