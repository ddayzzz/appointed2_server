from setuptools import setup
import sys

pyversion = sys.version_info

deps = ['aiohttp>=3', 'aiomysql', 'jinja2', 'async_generator'] if pyversion[:2] <= (3, 6) else ['aiohttp>=3', 'aiomysql', 'jinja2']

setup(name='appointed2',
          version='0.0.0.1',
          description='A simple web applications based on aiohttp',
          author='shu',
          author_email='wangshu214@live.cn',
          url='https://ddayzzz.wang',
          packages=['ap_database', 'ap_deploy', 'ap_http', 'ap_logger', 'ap_http.manager'],
          install_requires=deps,
          python_requires='>=3.6')

