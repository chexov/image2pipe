import logging
from multiprocessing import Queue
from unittest import TestCase

import cv2

import image2pipe

SCALE = scale = (320, 160)

VIDEO_URL = "/Users/chexov/testvideo/shuttle-flip.mp4"

logging.basicConfig()


class Image2PipeTest(TestCase):
    def test_rgb24_from_url(self):
        q = Queue()
        decoder = image2pipe.images_from_url(q, VIDEO_URL, fps="30", scale=SCALE)
        decoder.start()

        for i in range(30):
            fn, img = q.get()
            cv2.imshow("frame %d" % i, img)
            cv2.waitKey()
            cv2.destroyAllWindows()

    def test_stitch(self):
        fps = "30"
        out_url = "out.ts"
        scale = (1000, 552)

        bgr_q = Queue()

        decoder = image2pipe.images_from_url(bgr_q, VIDEO_URL, fps="30", scale=(1000, 552))
        decoder.start()

        FORMAT_MPEGTS = "mpegts"
        rtmpt = image2pipe.StitchVideoProcess(bgr_q, out_url, fps, scale, FORMAT_MPEGTS)
        rtmpt.start()

        rtmpt.join()


if __name__ == '__main__':
    Image2PipeTest().test_rgb24_from_url()
    Image2PipeTest().test_stitch()
