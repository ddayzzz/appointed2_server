from ap_database.orm import Model, StringField, FloatField

import time


class User(Model):

    __table__ = 'users'  # 表的位置
    passwd = StringField(column_type='varchar(50)')
    username = StringField(column_type='varchar(50)', primary_key=True)
    created_time = FloatField(default=time.time)
