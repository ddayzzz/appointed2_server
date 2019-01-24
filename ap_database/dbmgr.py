# coding=utf-8
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ["MySQLManager", "SQLManager"]
__doc__ = 'Appointed2 - SQL manager'
from ap_database.orm import ModelMetaclass, Model, TempModelMetaclass, TempModel, ViewTableMetaclass, ViewTable, BasicModel
from ap_logger.logger import make_logger
from asyncio import get_event_loop
import aiomysql
import abc

import sys
if sys.version_info[:2] <= (3, 6):
    from async_generator import async_generator, asynccontextmanager  # for python 3.6
else:
    from contextlib import asynccontextmanager  # python3.7


class SQLManager(object):

    def __init__(self):
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

    @abc.abstractmethod
    async def inner_select(self, sql, args, size=None, **kwargs):
        """
        select adapter
        :param pool:
        :param sql:
        :param args:
        :param size:
        :return:
        """
        pass

    @abc.abstractmethod
    async def inner_execute(self, sql, args, autocommit=True, **kwargs):
        pass

    @abc.abstractmethod
    async def close(self):
        pass

    @abc.abstractmethod
    async def connect(self, **kwargs):
        pass

    @abc.abstractmethod
    async def countNum(self, model_type, sql_where=None, args=None):
        pass


class MySQLManager(SQLManager):

    """
    使用 aiomysql 的异步 MySQL 连接器，目前仅仅对 删 改 进行异常检查
    """
    SQL_LOGGER = make_logger('MYSQLMGR')

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
        """
        关闭数据库的连接池
        :return:
        """
        self.SQL_LOGGER.debug('Closing a database connection pool...')
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
        self.pool = None

    async def connect(self, **kwargs):
        self.SQL_LOGGER.debug('Creating a database connection pool...')
        self.pool = await aiomysql.create_pool(
            host=self.host,
            port=self.port,
            user=self.username,
            password=self.password,
            db=self.dbname,
            charset=kwargs.get('charset', 'utf8'),
            # http://www.liaoxuefeng.com/discuss/001409195742008d822b26cf3de46aea14f2b7378a1ba91000/001451894920450a22651047f7f4a4ca2d0aea99d1452a2000
            autocommit=kwargs.get('autocommit', True),
            maxsize=kwargs.get('maxsize', 10),
            minsize=kwargs.get('minsize', 1),
            loop=self.loop
        )

    @property
    def connected(self):
        return self.pool is not None

    async def inner_select(self, sql, args, size=None, **kwargs):
        """
        perform a select operation. the default is DictCursor which is return a dict object.
        :param pool: connection pool
        :param sql: sql, placeholder is ?
        :param args: arguments for placeholders
        :param size: limited size
        :return: result, format is based on the type of cursor
        """
        self.SQL_LOGGER.debug('Perform: %s' % sql)
        async with self.pool.get() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql.replace('?', '%s'), args or ())
                if size:
                    rs = await cur.fetchmany(size)
                else:
                    rs = await cur.fetchall()
                self.SQL_LOGGER.debug('Row effected: %s' % cur.rowcount)
            return rs

    async def inner_execute(self, sql, args, autocommit=True, *kwargs):
        """
        This is proxy for performing the insert, update, delete on table
        :param pool:
        :param sql:
        :param args:
        :param autocommit:
        :return: return the number of affected rows
        """
        self.SQL_LOGGER.debug(sql)
        async with self.pool.get() as conn:
            if not autocommit:
                await conn.begin()
            try:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(sql.replace('?', '%s'), args)
                    affected = cur.rowcount
                if not autocommit:
                    await conn.commit()  # 如果没有自动保存修改就会立即修改
            except BaseException as e:
                if not autocommit:
                    await conn.rollback()
                raise
            return affected

    @asynccontextmanager
    async def inner_select_on_large(self, sql, args, **kwargs):
        """
        query large data with stream cursor. please ensure the connection by call the method 'ensureConnected'
        需要注意的是 https://blog.csdn.net/weixin_41287692/article/details/83545891
        1. 因为 SSCursor 是没有缓存的游标,结果集只要没取完，这个 conn 是不能再处理别的 sql，包括另外生成一个 cursor 也不行的。如果需要干别的，请另外再生成一个连接对象。
        2. 每次读取后处理数据要快，不能超过 60 s，否则 mysql 将会断开这次连接，也可以修改 SET NET_WRITE_TIMEOUT = xx 来增加超时间隔。
        使用额外库提供的 async 上下文管理器(python <= 3.6; 3.7 原生)避免 cur 在外部关闭, https://stackoverflow.com/questions/37433157/asynchronous-context-manager
        可以在 cursor 上调用 cursor 的相关异步方法获取数据 https://aiomysql.readthedocs.io/en/latest/cursors.html
        :param sql: sql, the format of placeholders is ?
        :param args: arguments for placeholder
        :param async_map_callback: asynchronous unary closure for format the data in result
        :return:return an instance of DictCursor in async contextmanager, you can call async method fetchone, fetchmany.
        """
        self.SQL_LOGGER.debug('Perform: %s' % sql)
        async with self.pool.get() as conn:
            async with conn.cursor(aiomysql.SSDictCursor) as cur:  # stream and dict cursor
                await cur.execute(sql.replace('?', '%s'), args or ())
                try:
                    yield cur
                finally:
                    await cur.close()

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
            await model_type_or_object.insert(self)
        elif isinstance(model_type_or_object, ModelMetaclass):
            # 是Model的元类
            obj = model_type_or_object(**fields_include_primary_keys)
            if not obj:
                raise ValueError('无法创建指定的对象‘%s’，通过属性：%s' % (str(model_type_or_object), ','.join(['%s=%s' % (k, v) for k, v in fields_include_primary_keys.items()])))
            await obj.insert(dbm=self)
        else:
            raise ValueError(str(model_type_or_object) + '不是 "Model"的一个子类。')

    async def query(self, model_type, **obj_primaryKeys):
        """
        查询一个表中的条目，返回ORM ： model_type的类。 由于视图目前不支持修改以及没有主码， 所以这个函数不适合 视图
        :param model_type: 模型，必须是Model的子类
        :param obj_primaryKeys: 主键（可以有多个）
        :return: 返回对象或者抛出错误
        """
        await self.ensureConnected()
        # if not isinstance(model_type, BasicModel):  # 只有元类的实例才判断继承关系
        #     raise ValueError(str(model_type) + '不是 "BasicModel" 的一个子类。该类必须支持投影操作')
        obj = await model_type.query_with_primary_keys(dbm=self, **obj_primaryKeys)  # 视图会自动出错
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
            await model_type_or_object.query_with_primary_keys(self)
        elif isinstance(model_type_or_object, ModelMetaclass):
            # 是Model的元类
            obj = await self.query(model_type_or_object, **obj_primaryKeys)
            if not obj:
                raise ValueError('没有找到条目：%s' % ','.join(['%s=%s' % (k, v) for k, v in obj_primaryKeys.items()]))
            await obj.delete(self)
        else:
            raise ValueError(str(model_type_or_object) + '不是 "Model"的一个子类。')

    async def update(self, model_type_or_object, ignore_not_exists=False, **kwargs):
        """
        更新对象或者数据库中的条目(主键除外)
        :param model_type_or_object: Model的子类实例或者是Metalass 的子类
        :param ignore_not_exists: 为 True 在不存在的这个对象的时候创建一个新的对象；否则抛出异常
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
                if not ignore_not_exists:
                    raise ValueError('没有找到条目：%s' % ','.join(['%s=%s' % (k, v) for k, v in kwargs.items()]))
                else:
                    # 根据现有的属性创建一个对象
                    await self.insert(model_type_or_object, **kwargs)
                    return
        else:
            raise ValueError(str(model_type_or_object) + '不是 "Model"的一个子类。')
        for k, v in kwargs.items():
            obj.__setattr__(k, v)
        await obj.save_change(self)

    async def queryAll(self, model_type, sql_where=None, args=None, **kwargs):
        """
        自定义查询, 正对一个已经存在的基本表、视图和临时表对象进行查询
        :param model_type: ORM元类的子类
        :param sql_where: SQL语句，使用?占位
        :param args: 占位符的实际值
        :param kwargs: 其他参数，orderBy 表示排序;limit 表示限制的结果过数量； toDict: 针对临时表。返回的结果是否保存为唯一的主键映射->其他的属性，默认关闭。注意需要在 ORM 中指定唯一的主键。注意，如果使用了排序那么无效。
        :return:
        """
        await self.ensureConnected()
        # if not isinstance(model_type, BasicModel):
        #     raise ValueError(str(model_type) + '不是 "BasicModel" 的一个子类。该类必须支持投影操作')
        obj = await model_type.query_all(self, where=sql_where, args=args, **kwargs)
        return obj

    async def countNum(self, model_type, sql_where=None, args=None):
        """
        count the number of records specified by primary keys
        :param model_type: Model type. not the instance of the model
        :param obj_primaryKeys: primary keys
        :return: number
        """
        await self.ensureConnected()
        # if not isinstance(model_type, BasicModel):
        #     raise ValueError(str(model_type) + '不是 "BasicModel"的一个子类。')
        num = await model_type.query_count(self, where=sql_where, args=args)
        return num



