from setuptools import setup

setup(
    name="easysh",
    version="1.0.0",
    license='MIT',
    description="an easy to execute shell commands in Python.",
    author='vince',
    author_email='yingjiaxin202@163.com',
    long_description=open('README.md', 'r').read(),
    long_description_content_type="text/markdown",
    packages={"easysh"},
    install_requires=["chardet"],
    keywords="shell sh",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Shells',
        'Topic :: Utilities',
        'Programming Language :: Python :: 3',
    ],
    url='https://github.com/yingjiaxin/easysh',

)


