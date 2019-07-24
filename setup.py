from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='image2pipe',
    version='0.1.9',
    author='Anton P. Linevich',
    author_email='anton@linevich.com',
    keywords="ffmpeg yuv image2pipe",
    packages=['image2pipe', ],
    scripts=[],
    url='https://github.com/chexov/image2pipe',
    license='LICENSE.txt',
    description='Simple ffmpeg wrapper for image2pipe which yields rawvideo frames from input video URL',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['tblib', 'numpy', 'websocket'],
    python_requires='>=3.2',
)
