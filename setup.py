import os
from setuptools import setup, find_packages


def read_file(filename):
    path = os.path.abspath(os.path.dirname(__file__))
    filepath = os.path.join(path, filename)
    try:
        return open(filepath).read()
    except OSError:
        return ''


def get_readme():
    """Return the README file contents. Supports text,rst, and markdown"""
    for name in ('README', 'README.rst', 'README.md'):
        if os.path.exists(name):
            return read_file(name)
    return ''


setup(
    name='django-azure-ad-auth-redux',
    version=__import__('azure_ad_auth').get_version().replace(' ', '-'),
    url='https://github.com/lanshark/django-azure-ad-auth-redux',
    author='Scott Sharkey',
    author_email='ssharkey@lanshark.com',
    description='Authenticated users using Azure Active Directory.',
    long_description=get_readme(),
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=read_file('requirements.txt'),
    classifiers=[
        'Environment :: Web Environment',
        'License :: OSI Approved :: BSD License',
        'Framework :: Django',
        'Programming Language :: Python',
    ],
)
