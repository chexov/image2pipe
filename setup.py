from distutils.core import setup

setup(
    name='image2pipe',
    version='0.1.0',
    author='Anton P. Linevich',
    author_email='anton@linevich.com',
    keywords="ffmpeg yuv image2pipe",
    packages=['image2pipe', ],
    scripts=[],
    url='https://github.com/chexov/image2pipe',
    license='LICENSE.txt',
    description='Simple ffmpeg wrapper for image2pipe',
    long_description=open('README').read(),
    install_requires=['tblib', 'numpy==1.14.2', 'opencv-python==3.4.0.12', 'websocket==0.2.1'],
    python_requires='>=2.6',
)
