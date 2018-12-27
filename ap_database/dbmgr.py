# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ["MySQLManager", "SQLManager"]
__doc__ = 'Appointed2 - SQL manager'
from ap_database.orm import ModelMetaclass, Model, TempModelMetaclass, TempModel
from ap_database.orm import create_pool as _createpool
from ap_database.orm import destory_pool as _despool
from asyncio import get_event_loop
import abc


class SQLManager(object):

    def __init__(self):
        pass

    @abc.abstractmethod
    async def connect(self):
        pass

    @abc.abstractmethod
    async def close(self):
        pass

    @abc.abstractmethod
    async def insert(self, model_type_or_object, **fields_include_primary_keys):
        pass

    @abc.abstractmethod
    async def query(self, model_type, **obj_primaryKeys):
        pass

    @abc.abstractmethod
    async def delete(self, model_type_or_object, **obj_primaryKeys):
        pass

    @abc.abstractmethod
    async def update(self, model_type_or_object, **kwargs):
        pass

    @abc.abstractmethod
    async def queryAll(self, model_type, sql_where=None, args=None, **kwargs):
        pass

    @abc.abstractmethod
    async def select(self, tempMetaModelObj, sql_where, args=None, toDict=False, **kwargs):
        pass


class MySQLManager(SQLManager):

    def __init__(self, username, password, dbname, host, port, loop=None):
        """
        创建一个对象
        :param username: 数据库连接的名称
        :param password: 密码
        :param dbname: 用户名
        :param host: 主机地址
        :param port: 端口
        :param loop: 事件循环
        """
        super(MySQLManager, self).__init__()
        self.username = username
        self.password = password
        self.dbname = dbname
        self.host = host
        self.port = port
        self.pool = None
        self.loop = loop
        if not loop:
            self.loop = get_event_loop()


    async def close(self):
        await _despool(self.pool)
        self.pool = None

    async def connect(self):
        self.pool = await _createpool(loop=self.loop, username=self.username, password=self.password, dbname=self.dbname, host=self.host, port=self.port)

    @property
    def connected(self):
        return self.pool

    async def ensureConnected(self):
        if not self.connected:
            await self.connect()

    async def insert(self, model_type_or_object, **fields_include_primary_keys):
        """
        向数据库中的某个表写入数据
        :param model_type_or_object: 可以是一个Model类（需要指定主键）。或者是Model的实例，忽略传入的属性
        :param fields_include_primary_keys: 属性，包含主键
        :return:
        """
        await self.ensureConnected()
        if isinstance(model_type_or_object, Model):
            # 是Model的字类的实例
            await model_type_or_object.save(self.pool)
        elif isinstance(model_type_or_object, ModelMetaclass):
            # 是Model的元类
            obj = model_type_or_object(**fields_include_primary_keys)
            if not obj:
                raise ValueError('无法创建指定的对象‘%s’，通过属性：%s' % (str(model_type_or_object), ','.join(['%s=%s' % (k, v) for k, v in fields_include_primary_keys.items()])))
            await obj.save(self.pool)
        else:
            raise ValueError(str(model_type_or_object) + "不是有效的的ORM模型")

    async def query(self, model_type, **obj_primaryKeys):
        """
        查询一个表中的条目，返回ORM ： model_type的类
        :param model_type: 模型，必须是Model的子类
        :param obj_primaryKeys: 主键（可以有多个）
        :return: 返回对象或者抛出错误
        """
        await self.ensureConnected()
        if not isinstance(model_type, ModelMetaclass):
            raise ValueError(str(model_type) + "不是有效的的ORM模型")
        obj = await model_type.find(self.pool, **obj_primaryKeys)
        return obj

    async def delete(self, model_type_or_object, **obj_primaryKeys):
        """
        删除一个条目
        :param model_type_orr_object: 可以是一个Model类（需要指定主键）。或者是Model的实例，忽略传入的主键
        :param obj_primaryKey:
        :return:
        """
        await self.ensureConnected()
        if isinstance(model_type_or_object, Model):
            # 是Model的字类的实例
            await model_type_or_object.remove(self.pool)
        elif isinstance(model_type_or_object, ModelMetaclass):
            # 是Model的元类
            obj = await self.query(model_type_or_object, **obj_primaryKeys)
            if not obj:
                raise ValueError('没有找到条目：%s' % ','.join(['%s=%s' % (k, v) for k, v in obj_primaryKeys.items()]))
            await obj.remove(self.pool)
        else:
            raise ValueError(str(model_type_or_object) + "不是有效的的ORM模型")

    async def update(self, model_type_or_object, **kwargs):
        """
        更新对象或者数据库中的条目
        :param model_type_or_object: Model的子类实例或者是Metalass 的子类
        :param kwargs: 更新的主键以及其他的属性
        :return:
        """
        await self.ensureConnected()
        obj = None
        if isinstance(model_type_or_object, Model):
            # 是Model的字类的实例
            obj = model_type_or_object
        elif isinstance(model_type_or_object, ModelMetaclass):
            # 是Model的元类
            obj = await self.query(model_type_or_object, **kwargs)
            if not obj:
                raise ValueError('没有找到条目：%s' % ','.join(['%s=%s' % (k, v) for k, v in kwargs.items()]))
        else:
            raise ValueError(str(model_type_or_object) + "不是有效的的ORM模型")
        for k, v in kwargs.items():
            obj.__setattr__(k, v)
        await obj.update(self.pool)

    async def queryAll(self, model_type, sql_where=None, args=None, **kwargs):
        """
        自定义查询
        :param model_type: ORM元类的子类
        :param sql_where: SQL语句，使用?占位
        :param args: 占位符的实际值
        :param kwargs: 其他的参数
        :return:
        """
        await self.ensureConnected()
        if not isinstance(model_type, ModelMetaclass):
            raise ValueError(str(model_type) + "不是有效的的ORM模型")
        result = await model_type.findAll(self.pool, sql_where, args, **kwargs)
        return result

    async def select(self, tempMetaModelObj, sql_where, args=None, toDict=False, **kwargs):
        """
        对临时表对象进行投影操作
        :param tempMetaModelObj: 临时表类
        :param sql_where: where 子句，必须使用的``分割不同的属性，同时前面加上多表的let名。如 table1->t1: t1.`postId`=?
        :param args: where 的参数, 如果没有使用?可以为空。注意如果右是一个表的属性，请在 where 中指定
        :param toDict: 返回的结果是否保存为唯一的主键映射->其他的属性，默认关闭。注意需要在 ORM 中指定唯一的主键。注意，如果使用了排序那么无效。
        :param kwargs: 其他参数，orderBy 表示排序;limit 表示限制的结果过数量
        :return:
        """
        if isinstance(tempMetaModelObj, TempModelMetaclass):
            if toDict and kwargs.get('orderBy', None):
                raise ValueError("不支持在结果为字典类型的情况下使用 orderby 子句。")
            await self.ensureConnected()
            # 执行 orm 的操作
            return await tempMetaModelObj.do(self.pool, sql_where, args, toDict=toDict, **kwargs)
        elif isinstance(tempMetaModelObj, TempModel):
            raise ValueError('不支持在非临时表的子类对象进行操作，请使用临时表"TempModel"的子类对象进行操作。')
        else:
            raise ValueError('不支持在非临时表上执行投影操作')

