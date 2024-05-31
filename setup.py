from setuptools import setup

setup(use_scm_version=True)


# setup(
#     name='tp-dcc',
#     use_scm_version=True,
#     setup_requires=[
#         'setuptools>=40.8.0',
#         'wheel'
#     ],
#     packages=find_packages(),
#     install_requires=[
#         # List your dependencies here
#         # 'numpy',
#         # 'requests',
#     ],
#     extras_require={
#         'docs': [
#             'sphinx',
#             'sphinx_rtd_theme',
#         ],
#         ':python_version < "3.8"': [
#             'dataclasses'
#         ]
#     },
#     entry_points={
#         'console_scripts': [
#             # Define command-line scripts here
#             # 'my_package=my_package.cli:main',
#         ],
#     },
#     author='Tomas Poveda',
#     author_email='tpovedatd@gmail.com',
#     description='Python package that streamline DCC workflows.',
#     long_description=open('README.rst').read(),
#     long_description_content_type='text/markdown',
#     url='https://github.com/tpoveda/tp-dcc',
#     license='MIT',
#     classifiers=[
#         'Programming Language :: Python :: 3',
#         'License :: OSI Approved :: MIT License',
#         'Operating System :: OS Independent',
#     ],
#     python_requires='>=3.7',
# )