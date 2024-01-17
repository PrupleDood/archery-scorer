from PIL import Image
import numpy as np
import cv2

from CardScorer.contour_funcs import find_close_groups


def process_base_img(filename):
    base_img = Image.open(filename)

    # Resize the image
    base_img = base_img.resize(
        (int(base_img.width / 2), int(base_img.height / 2)))

    # Convert to a cv2 image
    img = np.array(base_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Size of Gaussian kernel. Larger size -> stronger blur
    kernel_size = (5, 5)

    # Add Gaussian Blur
    blurred_img = cv2.GaussianBlur(img, kernel_size, 0)

    # Convert to gray
    gray_img = cv2.cvtColor(blurred_img, cv2.COLOR_BGR2GRAY)

    return gray_img


def contour_wrapper(img):

    def get_contours(func, *args, **kwargs):
        # Threshold the image to set black or white pixels
        _, thresh_image = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)

        # Find contours in the image
        contours, _ = cv2.findContours(thresh_image, cv2.RETR_TREE,
                                       cv2.CHAIN_APPROX_SIMPLE)

        # Iterate through the contours
        for i, contour in enumerate(contours):
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            func(approx, i, *args, **kwargs)

    return get_contours


def process_contours(img):
    area_arr = []
    cords_arr = []
    rect_arr = []

    @contour_wrapper(img)
    def filter_contours(approx, i):
        # Used for getting the middle points of the contour
        get_cords = lambda vals: (int(vals[0] + (vals[2] / 3)),
                                  int(vals[1] + (vals[3] / 1.5)))

        # get_wh = lambda vals: (int(vals[2]), int(vals[3]))

        area_arr.append(cv2.contourArea(approx))

        bounding_rect = cv2.boundingRect(approx)

        cords_arr.append(get_cords(bounding_rect))

        rect_arr.append(bounding_rect)

    # Convert arrays to numpy array
    cords_arr = np.array(cords_arr)
    area_arr = np.array(area_arr)
    rect_arr = np.array(rect_arr)

    return cords_arr, area_arr, rect_arr


# Functions for drawing on image
def draw_contours(image, group, cords_arr: np.ndarray):
    color = (0, 0, 0)
    font = cv2.FONT_HERSHEY_DUPLEX

    for i in group:
        index = np.where(cords_arr[:, 1][:, 0] == i[0])  #other time its i[0] idk

        if len(index[0]) == 0:
            continue

        coords = cords_arr[:, 0][index][0]

        cv2.putText(image, f"{coords[0]}", coords, font, 1, color, 1)

    result = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    cv2.imwrite("test.png", result)
    
    # cv2.imshow("window", result)
    # cv2.waitKey(0)


def draw_cords(image, cords, index, name="test.png"):
    color = (0, 0, 0)
    font = cv2.FONT_HERSHEY_DUPLEX

    for cord in cords:
        cv2.putText(image, f"{cord[index]}", cord, font, 1, color, 1)

    result = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    cv2.imwrite(name, result)

def draw_cords2(image, cords, name="test.png"):
    color = (0, 0, 0)
    font = cv2.FONT_HERSHEY_DUPLEX

    for i, cord in enumerate(cords):
        cv2.putText(image, str(i), cord, font, 1, color, 1)

    result = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    cv2.imwrite(name, result)


def draw_squares(image, rects):
    color = (0, 0, 0)
    font = cv2.FONT_HERSHEY_DUPLEX

    for cord in rects:
        x1, y1 = cord[0:2]
        x2, y2 = x1+cord[2], y1+cord[3]

        cv2.rectangle(image, (x1, y1), (x2, y2), (255,0,0), 2)

    result = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    cv2.imwrite("Boxes.png", result)


# def draw_scores(image, rect_rows, cord_rows, scores, flags):
#     color = (0, 0, 0)
#     font = cv2.FONT_HERSHEY_DUPLEX

#     flattened_rows = [rect[0][0][0] for rect in rect_rows]

#     sorted_mask = np.flip(np.argsort(flattened_rows, 0))

#     def add_rectangle(rect):
#         x1, y1 = rect[0:2]
#         x2, y2 = x1+rect[2], y1+rect[3]

#         cv2.rectangle(image, (x1, y1), (x2, y2), (255,0,0), 2)

#     for i in sorted_mask:
#         add_rectangle(rect_rows[i][0][0])

#     def add_score(cord, score):
#         cv2.putText(image, str(score), cord, font, 1, color, 1)

#     print(sorted_mask)

#     for i in sorted_mask:
#         for i2 in range(len(scores)):
#             print(len(cord_rows[i]))

#     # for i in range(len(scores)):
#     #     for i2 in sorted_mask:
#     #         print(scores[i], i2) if i2 != 5 else None
#         # [
#         #     add_score(cord_rows[i][i2][0], scores[i][i2])
#         #     for i2 in sorted_mask
#         #     if i != 5 and i2 != 5
#         # ]

#     result = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

#     cv2.imwrite("scores.png", result)