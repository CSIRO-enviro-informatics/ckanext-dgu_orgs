from setuptools import setup, find_packages

from ckanext.dgu_orgs import __version__

setup(
    name='ckanext-dgu_orgs',
    version=__version__,
    long_description="""\
    """,
    classifiers=[],
    namespace_packages=['ckanext', 'ckanext.dgu_orgs'],
    zip_safe=False,
    author='Open Knowledge Foundation',
    author_email='ashley.sommer@csiro.au',
    license='AGPL',
    description='CKAN DGU_ORGS',
    keywords='data packaging component tool server',
    install_requires=[
    ],
    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    package_data={},
    entry_points={
        'ckan.plugins': [
            'dgu_orgs = ckanext.dgu_orgs.plugin:DGUOrgsPlugin',
        ]
    }
)
