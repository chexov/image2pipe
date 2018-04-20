# Why

I need to extract frames from videos in order to feed into dnn pipeline.

this is the answer package.

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


q = Queue()
decoder = image2pipe.images_from_url(q, "shuttle-flip.mp4", fps="30", scale=(1000, 556))
decoder.start()

for i in range(30):
    fn, img = q.get()
    cv2.imshow("frame %d" % i, img)
    cv2.waitKey()
    cv2.destroyAllWindows()
```

