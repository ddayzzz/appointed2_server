# coding=utf-8
# created:2017-05-25
# description:用来创建连接池
# ref01：http://lib.csdn.net/snippet/python/47292
# ref02：https://github.com/wl356485255/pythonORM/blob/master/orm.py
# ref03：https://github.com/wl356485255/pythonORM/blob/master/ormTest.py
__author__ = 'Shu Wang <wangshu214@live.cn>'
__version__ = '0.0.0.1'
__all__ = ['create_args_string',
           'Field', 'StringField', 'BooleanField', 'IntegerField', 'FloatField', 'TextField', 'SmallIntField', 'DateTimeField',
           'ModelMetaclass', 'Model','TempModel', 'TempModelMetaclass',
           'ViewTable', 'ViewTableMetaclass']
__doc__ = 'Appointed2 - ORM define'



from ap_logger.logger import make_logger


_logger = make_logger('SQL')

def server_debug(msg):
    _logger.debug('SQL: %s' % (msg))


def server_warning(msg):
    _logger.warning('SQL: %s' % (msg))


def server_info(msg):
    _logger.info('SQL: %s' % (msg))



# 根据输入的参数生成的占位符列表
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ','.join(L)


# 定义Field类，负责保存(数据库)表的字段名和字段类型
class Field(object):
    # 表的字段的 表名前缀、名字、类型、是否为主键、默认值
    def __init__(self, prefix, name, column_type, primary_key, default):
        self.prefix = '' if not prefix else (prefix + '.')  # 我加上 . 作为处理
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    # 打印数据库 __reper__ __str__也是可以的
    def __str__(self):
        server_debug('<%s, %s, %s%s>' % (self.__class__.__name__, self.column_type, self.prefix, self.name))

# -*- 定义不同类型的衍生Field -*-
# -*- 表的不同列的字段的类型不一样
class StringField(Field):
    def __init__(self, prefix=None, name=None, primary_key=False, default=None, column_type='var'):
        super().__init__(prefix, name, column_type, primary_key, default)

    def __str__(self):  # 特例化的
        return 'StringField'


class BooleanField(Field):
    def __init__(self, prefix=None, name=None, default=None):
        super().__init__(prefix, name, 'boolean', False, default)

    def __str__(self):
        return 'BooleanField'


class IntegerField(Field):
    def __init__(self, prefix=None, name=None, primary_key=False, default=None):
        super().__init__(prefix, name, 'bigint', primary_key, default)

    def __str__(self):
        return 'IntegerField'


class SmallIntField(Field):
    def __init__(self, prefix=None, name=None, primary_key=False, default=None):
        super().__init__(prefix, name, 'smallint', primary_key, default)

    def __str__(self):
        return 'SmallIntField'


class FloatField(Field):
    def __init__(self, prefix=None, name=None, primary_key=False, default=None):
        super().__init__(prefix, name, 'real', primary_key, default)

    def __str__(self):
        return 'FloatField'


class TextField(Field):
    def __init__(self, prefix=None, name=None, default=None):
        super().__init__(prefix, name, 'Text', False, default)

    def __str__(self):
        return 'TextField'


class DateTimeField(Field):

    def __init__(self, prefix=None, name=None, primary_key=False, default=None):
        super(DateTimeField, self).__init__(prefix, name, 'datetime', primary_key, default)

    def __str__(self):
        return 'DateTimeField'


# -*-定义Model的元类

# 所有的元类都继承自type
# ModelMetaclass元类定义了所有Model基类(继承ModelMetaclass)的子类实现的操作

# -*-ModelMetaclass的工作主要是为一个数据库表映射成一个封装的类做准备：
# ***读取具体子类(user)的映射信息
# 创造类的时候，排除对Model类的修改
# 在当前类中查找所有的类属性(attrs)，如果找到Field属性，就将其保存到__mappings__的dict中，同时从类属性中删除Field(防止实例属性遮住类的同名属性)
# 将数据库表名保存到__table__中

# 完成这些工作就可以在Model中定义各种数据库的操作方法
class ModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        """
        __new__控制__init__的执行，所以在其执行之前
        :param cls: 代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)
        :param name:
        :param bases: 代表继承父类的集合
        :param attrs: 类的方法集合
        :return:
        """
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名词
        tableName = attrs.get('__table__', None) or name
        server_debug('Find model %s (Table: %s)' % (name, tableName))
        # 获取Field和主键的名称
        mappings = dict()
        fields = []
        primaryKeys = []  # 这个是主键
        for k, v in attrs.items():
            if isinstance(v, Field):
                server_info('Find field : %s ---> %s' % (k, v))
                mappings[k] = v
                # 是否是主键
                if v.primary_key:
                    primaryKeys.append(k)
                else:
                    fields.append(k)  # 所有非主键
        if len(primaryKeys) <= 0:  # 不可能没有主键
            raise ValueError('No primary key')
        for k in mappings.keys():  # 把所有属性相同的属性去掉
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        # primary keys的生成。生成的是主建的fields串
        primaryKey_fields = list(map(lambda f: '`%s`' % f, primaryKeys))
        primaryKeys_and_fields = ' and '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), primaryKeys))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_keys__'] = primaryKeys  # 这个是主键（关键字）
        attrs['__primary_key_fields__'] = primaryKeys_and_fields
        attrs['__fields__'] = fields

        attrs['__select__'] = 'select %s %s from `%s`' % (', '.join(primaryKey_fields), ',' + ', '.join(escaped_fields) if len(escaped_fields) > 0 else '', tableName)

        attrs['__insert__'] = 'insert into  `%s` (%s %s) values(%s)' % (
        tableName,', '.join(escaped_fields) + ', ' if len(escaped_fields) > 0 else '', ', '.join(primaryKey_fields), create_args_string(len(escaped_fields) + len(primaryKey_fields)))

        attrs['__update__'] = 'update `%s` set %s where %s' % (
        tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKeys_and_fields)

        attrs['__delete__'] = 'delete from  `%s` where %s' % (tableName, primaryKeys_and_fields)
        return type.__new__(cls, name, bases, attrs)


class TempModelMetaclass(type):

    def __new__(cls, name, bases, attrs):
        # 排除 TempModel
        if name == 'TempModel':
            return type.__new__(cls, name, bases, attrs)
        # server_debug('找到一个SQL数据模型 %s (数据表位: %s)' % (name, tableName))
        # 获取Field和主键的名称
        mappings = dict()
        # 链接的表名
        tables = attrs.get('__tables__', None)
        if not isinstance(tables, dict):
            raise ValueError("field '__tables__' not found in TemporaryModel")
        server_debug('Find temporary tables to join and its alias:%s' % ','.join(['%s ---> %s' % (tableName, letTableName) for tableName, letTableName in tables.items()]))
        # 各个属性
        fields = []
        # 一个主键,用于返回 dict 映射
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                server_info('找到 ORM映射: %s ---> %s' % (k, v))
                mappings[k] = v
                # 是否是主键
                if v.primary_key:
                    if not primaryKey:
                        primaryKey = (k, v)
                    else:
                        raise ValueError('Duplicated primary keys are not allowed in temporary joined tables')  # 临时表对象不支持定义组合的主键。唯一的主键可用于在投影操作返回一个 dict 对象结果
                if v.default:
                    raise ValueError("Temporary model are not allowed to allocate default value for a field")  # 临时表对象不支持为属性指定默认值
                if not v.prefix:
                    raise ValueError('Please specify alias for each tables to join')  # 单表、多表连接的临时表对象必指定属性的前缀表变量。例如：table1--->t1
                fields.append(k)  # 所有非主键
        for k in mappings.keys():  # 把所有属性相同的属性去掉
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))  # 所有属性构成的列表
        # primary keys的生成。生成的是主建的fields串
        attrs['__mappings__'] = mappings
        attrs['__fields__'] = fields
        # from 句，将链接的表构成一个变量，每个与
        attrs['__tables__'] = ','.join(['%s %s' % (tableName, letTableName) for tableName, letTableName in tables.items()])
        # select 子句: 注意 letName.`field` https://stackoverflow.com/questions/29451086/pymysql-syntax-when-using-two-tables
        attrs['__select__'] = 'select {s} from {t} '.format(s=','.join(['{prefix}`{fieldName}`'.format(prefix=field.prefix, fieldName=field.name if field.name else fn) for fn, field in mappings.items()]),  # 临时表可能存在属性不一致的情况
                                                            t=attrs['__tables__'])
        attrs['__primaryKey__'] = primaryKey
        return type.__new__(cls, name, bases, attrs)


class ViewTableMetaclass(type):

    """
    定义视图, 不允许定义主键和默认值, 同时不允许进行更新操作. 只有查询功能
    """

    def __new__(cls, name, bases, attrs):
        """
        __new__控制__init__的执行，所以在其执行之前
        :param cls: 代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)
        :param name:
        :param bases: 代表继承父类的集合
        :param attrs: 类的方法集合
        :return:
        """
        if name == 'ViewTable':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名词
        tableName = attrs.get('__table__', None) or name
        server_debug('Find view %s (View: %s)' % (name, tableName))
        # 获取Field和主键的名称
        mappings = dict()
        fields = []
        primaryKeys = []  # 这个是主键
        for k, v in attrs.items():
            if isinstance(v, Field):
                server_info('Find field : %s ---> %s' % (k, v))
                mappings[k] = v
                # 是否是主键
                if v.primary_key:
                    raise ValueError('Primary key is not allowed in view')
                else:
                    fields.append(k)  # 所有非主键

        for k in mappings.keys():  # 把所有属性相同的属性去掉
            attrs.pop(k)
        string_fields = list(map(lambda f: '`%s`' % f, fields))

        attrs['__mappings__'] = mappings  # 保存原始 Field 信息
        attrs['__table__'] = tableName

        attrs['__fields__'] = fields

        attrs['__select__'] = 'select %s from `%s`' % (', '.join(string_fields) if len(string_fields) > 0 else '*', tableName)

        return type.__new__(cls, name, bases, attrs)


# 定义ORM所有映射的基类：Model
# Model类的任意子类可以映射一个数据库表
# Model类可以看作是对所有数据库表操作的基本定义的映射
# 基于字典查询形式
# Model从dict继承，拥有字典的所有功能，同时实现特殊方法__getattr__和__setattr__，能够实现属性操作
# 实现数据库操作的所有方法，定义为class方法，所有继承自Model都具有数据库操作方法


class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"Model" objct has not attribute: %s' % (key))

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if not value:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                server_debug('Field \'%s\' uses default value \'%s\'' % (key, str(value)))
            setattr(self, key, value)
        return value

    @classmethod
    # 类方法有类变量cls传入，从而可以用cls做一些相关的处理。并且有子类继承时，调用该类方法时，传入的类变量cls是子类，而非父类。
    async def query_all(cls, dbm, where=None, args=None, **kw):
        """
        generate all code for quering all the records
        :param dbm: dbm
        :param where: where sql, the placeholder is ?
        :param args: arguments for placeholders
        :param kw: orderBy: string; limit: int
        :return: result
        """
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)

        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        # rs = await select(pool, ' '.join(sql), args)
        rs = await dbm.inner_select(' '.join(sql), args)  # perform the execute
        return [cls(**r) for r in rs]

    @classmethod
    async def query_count(cls, dbm, where=None, args=None):
        """
        find how many records in table. Always count *
        :param dbm:
        :param where:
        :param args:
        :return: number of records
        """
        sql = ['select COUNT(*) from `%s`' % cls.__table__]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await dbm.inner_select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return 0
        return rs[0]

    @classmethod
    async def query_with_primary_keys(cls, dbm, **primarykeys):
        """
        find an object by primary key
        :param dbm:
        :param primarykeys:
        :return: an object or None
        """
        # 主要 primary 的顺序
        pri_size = len(cls.__primary_keys__)
        if len(primarykeys) < pri_size:  # 可以多，但是不能少
            raise RuntimeError("Not enough primary key(s) specified")  # 主键长度不完整
        pri_keys = [primarykeys.get(pri_fieldName) for pri_fieldName in cls.__primary_keys__]

        rs = await dbm.inner_select('%s where %s' % (cls.__select__, cls.__primary_key_fields__), pri_keys, 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def insert(self, dbm):
        """
        insert this object into table
        :param dbm:
        :return: number of affected rows
        """
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.extend(list(map(self.getValueOrDefault, self.__primary_keys__)))

        # print(self.__insert__)
        rows = await dbm.inner_execute(self.__insert__, args)
        if rows != 1:
            server_warning('Failed to insert an entry, effected row(s): %d' % rows)  # 插入一条记录失败: 受影响 rows 的数量: %s
        return rows

    async def save_change(self, dbm):
        """
        update this in table except primary key
        :param dbm:
        :return: number of affected rows
        """
        args = list(map(self.getValue, self.__fields__))
        args.extend(list(map(self.getValue, self.__primary_keys__)))
        rows = await dbm.inner_execute(self.__update__, args)
        if rows != 1:
            server_warning('Failed to update an entry, effected row(s): %d' % rows)
        return rows

    async def delete(self, dbm):
        """
        delete this object in table
        :param dbm:
        :return: number of affected rows
        """
        args = list(map(self.getValue, self.__primary_keys__))
        rows = await dbm.inner_execute(self.__delete__, args)
        if rows != 1:
            server_warning('Failed to delete an entry, effected row(s): %d' % rows)
        return rows


class TempModel(dict, metaclass=TempModelMetaclass):

    def __init__(self, **kw):
        super(TempModel, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"TempModel" objct has not attribute: %s' % (key))

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    @classmethod
    async def select(cls, dbm, where, args, **kw):
        """
        在临时表中处理查询操作
        :param dbm: 数据库管理对象
        :param where: where 子句
        :param args: where 查询的参数
        :param kw: 其他参数，orderBy 表示排序;limit 表示限制的结果过数量;toDict 表示是否将结果转换为 dict 形式
        :return:
        """
        toDict = kw.get('toDict', False)
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)

        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            if toDict:
                raise ValueError("Can't transform result from list to dict object if toDict parameter is specified!")
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await dbm.inner_select(' '.join(sql), args)
        # 检查是否有主键
        if toDict:
            pkName, pkObj = cls.__primaryKey__  # 获取设置的主键
            finalKeyName = pkName if not pkObj.name else pkObj.name  # 最终使用的主键的名称
            if len(rs) > 0:
                # 有结果在才有意义
                target = dict()
                for item in rs:
                    key = item.get(finalKeyName)  # 这个必须要有
                    target[key] = cls(**item)  # 构建对象
                return target
            return rs
        else:
            return [cls(**r) for r in rs]


class ViewTable(dict, metaclass=ViewTableMetaclass):

    def __init__(self, **kw):
        super(ViewTable, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'"ViewTable" objct has not attribute: %s' % (key))

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    @classmethod
    async def select(cls, dbm, where, args, **kw):
        """
        在视图中处理查询操作, 其实可以复用 临时表的查询
        :param dbm: 数据库管理对象
        :param where: where 子句
        :param args: where 查询的参数
        :param kw: 其他参数，orderBy 表示排序;limit 表示限制的结果过数量;
        :return:
        """
        sql = [cls.__select__]

        if where:
            sql.append('where')
            sql.append(where)

        if args is None:
            args = []

        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)

        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?,?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await dbm.inner_select(' '.join(sql), args)

        return [cls(**r) for r in rs]



