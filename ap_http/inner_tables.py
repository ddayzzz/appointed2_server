# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ["User"]
__doc__ = 'Appointed2 - inner tables for ap_http server'


from ap_database.orm import Model, StringField, BooleanField, FloatField
import time
import uuid


def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)


class User(Model):

    __table__ = 'ap_users'  # 表的位置
    id = StringField(primary_key=True, default=next_id, column_type='varchar(50)')  # 自动计算时间作为默认的id
    email = StringField(column_type='varchar(50)')
    passwd = StringField(column_type='varchar(50)')
    admin = BooleanField(default=lambda:False)
    username = StringField(column_type='varchar(50)')
    image = StringField(column_type='varchar(500)')
    created_at = FloatField(default=time.time)
