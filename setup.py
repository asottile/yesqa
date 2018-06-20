from setuptools import setup

setup(
    name='yesqa',
    description='Automatically remove unnecessary `# noqa` comments.',
    url='https://github.com/asottile/yesqa',
    version='0.0.6',
    author='Anthony Sottile',
    author_email='asottile@umich.edu',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    install_requires=['flake8', 'tokenize-rt>=2'],
    py_modules=['yesqa'],
    entry_points={'console_scripts': ['yesqa = yesqa:main']},
)
