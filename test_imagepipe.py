import logging
from multiprocessing import Queue
from unittest import TestCase

import cv2

import image2pipe

SCALE = scale = (320, 160)

VIDEO_URL = "/Users/chexov/testvideo/shuttle-flip.mp4"

logging.basicConfig()


class Image2PipeTest(TestCase):
    def test_min_params(self):
        q = Queue()
        decoder = image2pipe.images_from_url(q, VIDEO_URL)
        decoder.start()

        for i in range(30):
            fn, img = q.get()
            cv2.imshow("frame %d" % i, img)
            cv2.waitKey()
            cv2.destroyAllWindows()

    def test_rgb24_from_url(self):
        q = Queue()
        decoder = image2pipe.images_from_url(q, VIDEO_URL, fps="30", scale=SCALE)
        decoder.start()

        for i in range(30):
            fn, img = q.get()
            cv2.imshow("frame %d" % i, img)
            cv2.waitKey()
            cv2.destroyAllWindows()

    def test_vf(self):
        q = Queue()
        # decoder = image2pipe.images_from_url(q, VIDEO_URL, fps="30", scale=SCALE, vf=["cropdetect=24:16:0"])
        decoder = image2pipe.images_from_url(q, VIDEO_URL, fps="30", scale=SCALE, vf=["crop=224:224:0:36"])
        decoder.start()

        fn, img = q.get()
        cv2.imshow("frame %d" % 0, img)
        cv2.waitKey()
        cv2.destroyAllWindows()

    def test_stitch(self):
        fps = "30"
        out_url = "out.ts"
        # out_url = "out.mov"
        scale = (1000, 552)

        bgr_q = Queue()

        decoder = image2pipe.images_from_url(bgr_q, VIDEO_URL, fps="30", scale=(1000, 552))
        decoder.start()

        # rtmpt = image2pipe.StitchVideoProcess(bgr_q, out_url, fps, scale, muxer="mov")
        FORMAT_MPEGTS = "mpegts"
        rtmpt = image2pipe.StitchVideoProcess(bgr_q, out_url, fps, scale, FORMAT_MPEGTS)
        rtmpt.start()

        rtmpt.join()


if __name__ == '__main__':
    Image2PipeTest().test_min_params()
    Image2PipeTest().test_vf()
    Image2PipeTest().test_rgb24_from_url()
    Image2PipeTest().test_stitch()
