import os
from setuptools import setup

README = """
Django REST Swagger

An API documentation generator for Swagger UI and Django REST Framework version 2.3+

Installation
From pip:

pip install django-rest-swagger

Docs & details @
https://github.com/marcgibbons/django-rest-swagger
"""

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-rest-hal',
    version='0.0.2',
    packages=['django_rest_hal'],
    # package_data={'django_rest_hal': ['django_rest_hal/*']},
    # include_package_data=True,
    license='FreeBSD License',
    description='HAL Implementation for Django REST Framework 2.3+',
    long_description=README,
    install_requires=[
        'django>=1.6',
        'djangorestframework>=2.3.5',
    ],

    url='http://github.com/seebass',
    author='Sebastian Bredehöft',
    author_email='bredehoeft.sebastian@gmail.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
