# -*- coding: utf-8 -*-
"""项目总路由：全部交给 接口 app。"""
from django.urls import include, path

urlpatterns = [
    path('', include('接口.urls')),
]
