from setuptools import find_packages, setup

setup(
    name='django-keyset-pagination-plus',
    version='0.9.0',
    description='Keyset Pagination (seek method) for django.',
    long_description=open('README.md').read(),
    url='https://bitbucket.org/schinckel/django-keyset-pagination',
    author='Matthew Schinckel',
    author_email='matt@schinckel.net',
    packages=find_packages('src', exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    package_dir={'': 'src'},
    include_package_data=True,
    package_data={},
    python_requires='>=2.7',
    install_requires=[
        'django'
    ],
    setup_requires=["pytest-runner", ],
    tests_require=["pytest", ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
