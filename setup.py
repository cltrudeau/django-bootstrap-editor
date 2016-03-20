import os

VERSION = '0.1.0'

readme = os.path.join(os.path.dirname(__file__), 'README.rst')
long_description = open(readme).read()

SETUP_ARGS = dict(
    name='django-bootstrap-editor',
    version=VERSION,
    description=('Django tool for creating and editing Bootstrap (3+) '
        'CSS files'),
    long_description=long_description,
    url='https://github.com/cltrudeau/django-bootstrap-editor',
    author='Christopher Trudeau',
    author_email='ctrudeau+pypi@arsensa.com',
    license='MIT',
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
#        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='django,bootstrap,CSS,editor',
    test_suite="load_tests.get_suite",
    install_requires=[
        'Django>=1.8',
        'django-awl>=0.11.1',
        'wrench>=0.8',
        'six>=1.10.0',
    ],
#    tests_require=[
#        'mock>=1.3.0',
#    ]
)

if __name__ == '__main__':
    from setuptools import setup, find_packages

    SETUP_ARGS['packages'] = find_packages()
    setup(**SETUP_ARGS)
