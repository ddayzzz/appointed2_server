from ap_http.route import get
__all__ = ['hello_word', 'hello', 'show_user_info', 'test', 'slow_show']


@get('/get')
async def test(dbm):
    from model import User
    await dbm.ensureConnected()
    i = await dbm.countNum(User, sql_where='username=?', args=('test', ))
    return i

@get('/')
def hello_word(sb):
    # return 'Hello word, {}!'.format(sb)
    return {'__template__': 'hello.html', 'name': 'sss'}


@get('/hello/{name}')
def hello(name):
    return {'__template__': 'hello.html', 'name': name}

@get('/show')
async def show_user_info(dbm):
    from ap_samples.http_app import model
    await dbm.ensureConnected()
    async with dbm.inner_select_on_large(sql='select * from users', args=tuple()) as c:
        while True:
            item = await c.fetchone()
            if not item:
                break
            print(item)
    # items = await dbm.queryAll(model.User, sql_where='passwd <> ?', args=('111', ))
    # print(items)

@get('/slow')
async def slow_show(dbm):
    import asyncio
    await dbm.ensureConnected()
    async with dbm.inner_select_on_large(sql='select * from users', args=tuple()) as c:
        while True:
            await asyncio.sleep(5)
            raise TimeoutError('SV')
            item = await c.fetchone()
            if not item:
                break
            print(item)