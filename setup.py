from setuptools import setup, find_packages

setup(
    name='myfi',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'sqlalchemy',
        'ofxparse',
    ],
    entry_points='''
        [console_scripts]
        myfi=myfi.cli:cli
    ''',
)
