import time
from math import sqrt
from multiprocessing import Pool, Queue
import cv2
import mouse
import numpy as np
from Arm import HandTracker
from setting import Settings
from ctypes import *


def init_pool(d_b):
    global detection_buffer
    detection_buffer = d_b


def detect_object(frame):
    detection_buffer.put(frame)


def distance(a, b):
    return sqrt((a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def direction(start, end, inverse_x=True):
    return start[0] - end[0] if inverse_x else end[0] - start[0], end[1] - start[1]


def middle(a, b):
    return (a[0] + b[0]) / 2, (a[1] + b[1]) / 2


def subtraction(a, b):
    return a[0] - b[0], a[1] - b[1]


def show():
    while True:
        frame = detection_buffer.get()

        if frame is not None:
            cv2.imshow("Video", frame)
        else:
            break
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    return


def camera_to_local_per(pos):
    return (camera_width - pos[0] - start_pos[0]) / loc_width, (pos[1] - start_pos[1]) / loc_height


def local_per_to_global(pos):
    pos = list(pos)
    if pos[0] > 1:
        pos[0] = 1
    if pos[1] > 1:
        pos[1] = 1
    if pos[1] < 0:
        pos[1] = 0
    if pos[0] < 0:
        pos[0] = 0
    return pos[0] * global_width, pos[1] * global_height,


def main():
    global image
    tracker = HandTracker()
    start_mouse_pos = mouse.get_position()
    move = False
    init = True
    clickedL = False
    clickedR = False
    scrolled = False
    last_812_scroll = (0, 0)
    while True:
        success, image = cap.read()
        if success:
            image = tracker.handsFinder(image)
            lmList, absLm = tracker.positionFinder(image)
            if len(lmList) != 0:

                now_812_scroll = middle(lmList[8][1:], lmList[12][1:])
                if init:
                    init = False
                    last_812_scroll = middle(lmList[8][1:], lmList[12][1:])
                else:
                    print(last_812_scroll[1] - now_812_scroll[1], scrolled)
                    if scrolled:
                        scrolled = False
                        continue
                    if now_812_scroll[1] - last_812_scroll[1] > settings.threshold_scroll:

                        scrolled = True
                        mouse.wheel(delta=-settings.scroll_step)
                    elif now_812_scroll[1] - last_812_scroll[1] < -settings.threshold_scroll:
                        scrolled = True
                        mouse.wheel(delta=settings.scroll_step)
                    last_812_scroll = now_812_scroll

                loc_pos = camera_to_local_per(lmList[4][1:])
                if distance(lmList[4], lmList[8]) < settings.threshold_drag:
                    mouse.move(*local_per_to_global(loc_pos), duration=0.1)
                if distance(lmList[4], lmList[12]) < settings.threshold_drag:
                    if not clickedL:
                        mouse.click("left")
                        clickedL = True
                else:
                    clickedL = False
                if distance(lmList[4], lmList[16]) < settings.threshold_drag:
                    if not clickedR:
                        mouse.click("right")
                        clickedR = True
                else:
                    clickedR = False
            else:
                init = True
        else:
            break
        if shw_image:
            image = cv2.flip(image, 1)
            image = cv2.rectangle(image, pt1=start_pos,
                                  pt2=end_pos, color=(255, 0, 0), thickness=3)
            pool.apply_async(detect_object, args=(image,))
    if shw_image:
        detection_buffer.put(None)
        show_future.get()


image = []
settings = Settings()
shw_image = False
cap = cv2.VideoCapture(0)
camera_width = int(cap.get(3))
camera_height = int(cap.get(4))

global_width = windll.user32.GetSystemMetrics(0)
global_height = windll.user32.GetSystemMetrics(1)

threshold_window = settings.threshold_window
start_pos = (camera_width // threshold_window, camera_height // threshold_window)
end_pos = (camera_width - camera_width // threshold_window, camera_height - camera_height // threshold_window)
loc_width = camera_width - 2 * (camera_width // threshold_window)
loc_height = camera_height - 2 * (camera_height // threshold_window)
if __name__ == "__main__":
    if shw_image:
        detection_buffer = Queue()
        pool = Pool(6, initializer=init_pool, initargs=(detection_buffer,))
        show_future = pool.apply_async(show)
    main()
