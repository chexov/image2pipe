# Why

I need to extract decoded frames from videos in order to feed DNN pipeline.

This is the answer package.

# Install

```
pip install image2pipe
```

# Usage

```
from multiprocessing import Queue
import logging
import cv2

import image2pipe

logging.basicConfig()


q = Queue(maxsize=4)
decoder = image2pipe.images_from_url(q, "shuttle-flip.mp4", fps="30", scale=(1000, 556))
decoder.start()

 for pair in yield_from_queue(q):
        fn, img = pair
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        cv2.imshow("gray", gray)
        cv2.waitKey()
        cv2.destroyAllWindows()
```

