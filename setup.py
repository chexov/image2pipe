from distutils.core import setup

setup(
    name='image2pipe',
    version='0.0.1',
    author='Anton P. Linevich',
    author_email='anton@linevich.com',
    keywords="ffmpeg yuv image2pipe",
    packages=['image2pipe', ],
    scripts=[],
    url='https://github.com/chexov/image2pipe',
    license='LICENSE.txt',
    description='Simple ffmpeg wrapper for image2pipe',
    long_description=open('README.md').read(),
    install_requires=['tblib', 'numpy'],
    python_requires='>=2.6',
)
