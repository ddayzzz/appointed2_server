from ap_http.route import get
__all__ = ['hello_word', 'hello', 'show_user_info', 'test']


@get('/get')
async def test(dbm):
    from model import User
    await dbm.ensureConnected()
    i = await User.findNumber(dbm.pool, where='username=?', args=('test', ))
    return i

@get('/')
def hello_word(sb):
    return 'Hello word, {}!'.format(sb)


@get('/hello/{name}')
def hello(name):
    return {'__template__': 'hello.html', 'name': name}

@get('/show')
async def show_user_info(dbm):
    from ap_samples.http_app import model
    await dbm.ensureConnected()
    async with dbm.inner_select_on_large(sql='select * from users where username=?', args=('test', )) as c:
        print(await c.fetchone())