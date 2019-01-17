from setuptools import setup

setup(name='appointed2',
      version='0.0.0.1',
      description='A simple web applications based on aiohttp',
      author='shu',
      author_email='wangshu214@live.cn',
      url='https://ddayzzz.wang',
      packages=['ap_database', 'ap_deploy', 'ap_http', 'ap_logger'],
      install_requires=['aiohttp>=3'],
      python_requires='>=3.5.3')
