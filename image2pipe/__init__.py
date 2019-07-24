#!/usr/bin/env python
# encode: utf-8

import collections
import itertools
import json
import logging
import multiprocessing
import subprocess
import sys
from multiprocessing import Queue
from time import time

import numpy
import websocket

from . import ffmpeg
from . import utils

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class SuperliveWebsocketProcess(multiprocessing.Process):
    def __init__(self, q_out, ws_url):
        """

            :type ws_url: str
            :type q_out: queues.Queue
            """
        super(SuperliveWebsocketProcess, self).__init__()
        self.ws_url = ws_url
        self.q_out = q_out

    def run(self):
        def on_open(ws):
            log.debug("super live opened for %s" % self.ws_url)

        def frame(ws, msg):
            self.q_out.put(msg)

        def on_error(ws, error):
            log.error("socket error %s" % error)
            self.q_out.put(None)
            self.q_out.close()

        def on_close(ws):
            log.debug("done with live. socket closed! " + self.ws_url)
            self.q_out.put(None)
            self.q_out.close()

        ws = websocket.WebSocketApp(self.ws_url,
                                    on_open=on_open,
                                    on_close=lambda _ws: on_close(_ws),
                                    on_error=lambda _ws, _er: on_error(_ws, _er),
                                    on_message=lambda _ws, _msg: frame(_ws, _msg)
                                    )
        ws.run_forever()


class DecodeH264Process(multiprocessing.Process):
    def __init__(self, h264_frames_q, bgr24_frames_q, ss="00:00:00", fps="30", scale=(1000, 562)):
        super(DecodeH264Process, self).__init__()
        self.ss = ss
        self.fps = fps
        self.scale = scale
        self.h264q = h264_frames_q
        self.bgrq = bgr24_frames_q

    def run(self):
        ffmpeg_p = ffmpeg.bgr24_from_stdin_subp(self.fps, self.scale)

        bgr_p = multiprocessing.Process(
            target=lambda: ffmpeg.enqueue_frames_from_output(ffmpeg_p, self.bgrq, self.scale))
        bgr_p.daemon = True
        bgr_p.start()

        log.debug("decoder() bgrq is %s" % str(self.bgrq))
        while True:
            bb = self.h264q.get()

            if bb is None:
                self.bgrq.put(None)
                # self.bgrq.close()
                log.info("done with decoding!")
                return

            # log.debug("written %s to decoder" % len(bb))
            ffmpeg_p.stdin.write(bb)


def _emitt_image_output(_proc, _emitter, _scale):
    """

       :type _emitter: rx.Emitter
       :type _scale: tuple
       :type _proc: subprocess.Popen
       """
    try:
        e = None
        frame_counter = itertools.count()
        while not _proc.poll():
            img_size = _scale[0] * _scale[1] * 3
            bb = _proc.stdout.read(img_size)
            if len(bb) > 0:
                try:
                    ndarr = numpy.frombuffer(bb, dtype=numpy.uint8).reshape((_scale[1], _scale[0], 3))
                    fn = next(frame_counter)
                    _emitter.onNext((fn, ndarr))
                except Exception as err:
                    log.error("%s" % err)

            e = _proc.poll()
            if e >= 0 and len(bb) == 0:
                break

        log.debug("bye ffmpeg %d" % e)
        if e == 0:
            _emitter.onComplete()
        elif e > 0:
            _emitter.onError(RuntimeError("ffmpeg exits with code %d" % e))
    except Exception:
        _emitter.onError(sys.exc_info()[1])


def images_from_url(q: Queue, video_url: str, ss: str = "00:00:00", fps: str = None, scale: tuple = (224, 224),
                    pix_fmt: str = "bgr24", vf: list = None):
    """

    :param ss: start second in a format of time "00:00:00"
    :param pix_fmt: rawcodec image format bgr24 or rgb24
    :type scale: tuple (width, height)
    :type fps: str
    :type video_url: str
    :type ss: str
    :type pix_fmt: str
    :type q: queues.Queue
    """

    ffmpeg_p = ffmpeg.images_from_url_subp(fps, scale, video_url, ss, image_format=pix_fmt, vf=vf)

    if scale is None:
        probe = ffprobe(video_url)
        vstream = first_video_stream(probe)
        scale = (int(vstream['width']), int(vstream['height']))
    reader_p = multiprocessing.Process(target=lambda: ffmpeg.enqueue_frames_from_output(ffmpeg_p, q, scale))
    reader_p.daemon = True
    return reader_p


def ffprobe(url):
    p = subprocess.Popen(["ffprobe", "-v", "error", "-show_streams", "-print_format", "json", url],
                         stdout=subprocess.PIPE)
    p.wait()
    if p.poll() != 0:
        raise RuntimeError("ffprobe exit code is %s" % p.poll())

    ffp = json.loads(p.stdout.read().decode("utf-8"))
    return ffp


def first_video_stream(ffprobe_json: dict):
    video_stream = list(filter(lambda s: "video" == s.get("codec_type"), ffprobe_json.get("streams")))
    if video_stream:
        return video_stream[0]
    else:
        return None


class StitchVideoProcess(multiprocessing.Process):
    def __init__(self, frames_q: Queue, out_url: str, fps: str, scale: tuple, pix_fmt: str = "bgr24",
                 muxer: str = 'flv'):
        """

        :type frames_q: queues.Queue
        """
        super(StitchVideoProcess, self).__init__()
        self.fps = fps
        self.scale = scale
        self.out_url = out_url
        self.q = frames_q
        self.container = muxer
        self.pix_fmt = pix_fmt

    def run(self):
        try:
            scale_str = "x".join(map(lambda x: str(x), self.scale))
            cmd = ["ffmpeg", '-v', 'error', '-y', '-f', 'rawvideo',
                   '-vcodec', 'rawvideo', '-s', scale_str, '-pix_fmt', self.pix_fmt, '-r', str(self.fps),
                   '-i', '-', '-an',
                   '-pix_fmt', 'yuv420p', '-vcodec', 'libx264', '-profile:v', 'baseline', '-crf', '21', '-g',
                   str(self.fps),
                   '-b:v', '2400k',
                   '-f', self.container, self.out_url]

            log.debug("popen '%s'" % " ".join(cmd))
            ffmpeg_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, bufsize=3 * self.scale[0] * self.scale[1])

            frames_stack = collections.deque()
            frames_counter = itertools.count()
            next_fn = next(frames_counter)

            start_time = time()
            frames_processed = 0

            for pair in utils.yield_from_queue(self.q, timeout_sec=30.2):
                fn, inimg = pair
                # log.debug("got pair for stiching fn:%s" % fn)

                # validate inimg size
                height, width = inimg.shape[:2]
                # log.debug("stich input size %sx%s;" % (width, height))
                assert height == self.scale[1], "height is different %s != %s" % (height, self.scale[1])
                assert width == self.scale[0], "width is different %s != %s" % (width, self.scale[0])

                frames_stack.append(pair)
                if fn == next_fn:
                    frames_stack = collections.deque(sorted(frames_stack, key=lambda p: p[0]))

                    # log.debug("draining stack... next_frame=%s stack size=%s" % (next_fn, len(frames_stack)))
                    while len(frames_stack) > 0:
                        p = frames_stack.popleft()
                        fn = p[0]
                        img = p[1]
                        if fn == next_fn:
                            try:
                                ffmpeg_proc.stdin.write(img)
                            except Exception:
                                log.error("rtmpt ffmpeg failed? exiting", exc_info=True)
                                # self.frames_q.close()
                                self.terminate()
                                return

                            next_fn = next(frames_counter)
                        else:
                            frames_stack.appendleft(p)
                            break
                        frames_processed += 1
                        if frames_processed % 1000 == 0:
                            print('******** stitch fps = %.02f **********' % (frames_processed / (time() - start_time)))
                            start_time = time()
                            frames_processed = 0

            log.info("done with stitching!")
            # self.frames_q.close()
            ffmpeg_proc.stdin.close()
            ffmpeg_proc.wait()
            return
        except Exception:
            log.error("video stitch exited. end of stream?", exc_info=True)
