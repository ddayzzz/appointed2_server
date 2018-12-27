from setuptools import setup

setup(name='appointed2',
      version='0.0.0.1',
      description='A simple web server based on aiohttp',
      author='shu',
      author_email='wangshu214@live.cn',
      url='https://ddayzzz.wang',
      license='MIT',
      keywords='aiohttp async',
      project_urls={
            'Documentation': 'https://github.com/ddayzzz/appointed2_server',
            'Funding': 'https://ddayzzz.wang',
            'Source': 'https://github.com/ddayzzz/appointed2_server',
            'Tracker': 'https://github.com/ddayzzz/appointed2_server',
      },
      packages=['appointed2'],
      install_requires=['aiohttp>=3'],
      python_requires='>=3.5.3'
     )
