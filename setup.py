from setuptools import setup

with open("README") as f:
    long_description = f.read()

setup(
    name='nbastreams',

    version='1.0',

    description='Tool to watch NBA games',
    long_description=long_description,

    url='https://github.com/erudman21/nbastreams',

    # Author main details
    author='Eli Rudman',
    author_email='erudman21@gmail.com',

    # Really basic classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Anyone!'
    ],

    keywords='NBA streams',

    install_requires=[
        'praw',
        'tkinter',
        'urllib',
        'bs4',
        'webbrowser'
    ]

)