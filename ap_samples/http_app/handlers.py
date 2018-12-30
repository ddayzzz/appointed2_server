from ap_http.route import get
__all__ = ['hello_word', 'hello', 'show_user_info']

@get('/')
def hello_word(sb):
    return 'Hello word, {}!'.format(sb)


@get('/hello/{name}')
def hello(name):
    return {'__template__': 'hello.html', 'name': name}

@get('/show')
async def show_user_info(username, dbm):
    from ap_samples.http_app import model
    res = await dbm.query(model_type=model.User, username=username)
    k = {'__template__': 'show.html'}
    k.update(res)
    return k
