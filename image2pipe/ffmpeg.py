#!/usr/bin/env python
import copy
import itertools
import logging
import multiprocessing
import subprocess

import numpy
from numpy.ma import frombuffer

FFMPEG_BIN = "ffmpeg"
log = logging.getLogger(__name__)


def bgr24_from_stdin_subp(_fps, _scale):
    """
    Usage:
    sp = bgr24_from_stdin_subp(fps, scale)
    sp.stdin.write(rawvideo)

    :param _fps: 
    :param _scale: 
    :return: 
    """
    vf_scale = "fps=%s,scale=%sx%s" % (_fps, _scale[0], _scale[1])
    cmd = [FFMPEG_BIN, "-v", "error",
           "-i", "pipe:0",
           "-an", "-sn", "-f", "image2pipe",
           "-vcodec", "rawvideo", "-pix_fmt", "bgr24", "-vf", vf_scale,
           "-y", "pipe:1"]
    log.debug("popen %s" % " ".join(cmd))
    ffmpeg_p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return ffmpeg_p


def images_from_url_subp(_fps, _scale, _url, ss=None, image_format='bgr24', vf: list = None):
    """
    Usage:
    p = images_from_url_subp(fps, scale, url)
    :type ss: str

    :param vf: ffmpeg -vf filters 
    :param image_format: str with ffmpeg's pix_fmt
    :param ss: "00:00:00"
    :param _fps: 
    :param _scale: 
    :param _url: 
    :return: 
    """
    cmd = [FFMPEG_BIN, "-v", "error"]
    if ss:
        cmd.append("-ss")
        cmd.append(ss)
    cmd += ["-i", _url, '-an', '-sn', "-f", "image2pipe", "-vcodec", "rawvideo", "-pix_fmt", image_format]

    if vf:
        _vf = copy.copy(vf)
    else:
        _vf = []

    if _fps:
        _vf.append("fps=%s" % _fps)
    if _scale:
        _vf.append("scale=%sx%s" % (_scale[0], _scale[1]))
    if len(_vf) > 0:
        cmd.append("-vf")
        cmd.append(",".join(_vf))
    cmd.append("-")
    log.debug("popen %s" % " ".join(cmd))
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, bufsize=10 ** 8)


def enqueue_frames_from_output(_proc, _qout, scale):
    """

    :type scale: tuple
    :type _proc: subprocess.Popen
    :type _qout: queues.Queue
    """
    e = None
    frame_counter = itertools.count()
    while multiprocessing.current_process().is_alive():
        img_size = scale[0] * scale[1] * 3
        bb = _proc.stdout.read(img_size)
        if len(bb) > 0:
            try:
                ndarr = frombuffer(bb, dtype=numpy.uint8).reshape((scale[1], scale[0], 3))
                fn = next(frame_counter)
                _qout.put((fn, ndarr))
            except Exception as err:
                log.error("%s" % err)

        e = _proc.poll()
        # log.debug("%s bb size %d" % (e, len(bb)))
        if e >= 0 and len(bb) == 0:
            break

    log.debug("bye ffmpeg %d" % e)
    if e == 0:
        _qout.put(None)
        _qout.close()
    elif e > 0:
        _qout.put(None)
        _qout.close()
        raise RuntimeError("ffmpeg exits with code %d" % e)
