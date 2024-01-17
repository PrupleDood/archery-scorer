import numpy as np

from CardScorer.image_funcs import process_base_img, process_contours
from CardScorer.contour_funcs import get_anchor_pos
from CardScorer.score_funcs import get_scores, get_valid_indice, divide_into_rows, check_scores


class ScoreCard():

    MUTLIPLE = 0
    SINGLE = 1

    def __init__(self, filename, score_type:int = 0) -> None:
        # Process the base image to scaled down and gray scale
        self.gray_image = process_base_img(filename)

        self.TYPE = score_type if score_type else ScoreCard.MUTLIPLE

        self.scores, self.flags, self.rows, self.rect_rows = ScoreCard._estimate_score(self.gray_image, self.TYPE)

        # self.sum_score = np.sum(self.scores)
        self.sum_score = 0


    def _estimate_score(image:np.ndarray, TYPE: int):
        # Process countours and get arrays
        cords_arr, area_arr, rect_arr = process_contours(image)

        # Get anchor pos and anchor y cords
        # anchor_pos, anchor_cords = get_anchor_pos2(sorted_groups, cords_arr)

        anchor_cords, x_mean = get_anchor_pos(cords_arr, len(image))

        anchor_indexes = [i for i, cords in enumerate(cords_arr) if cords[0] in anchor_cords and cords[1] in anchor_cords]

        anchor_width = round(np.mean([width for width in rect_arr[anchor_indexes, 2]]), 2)
        anchor_height = round(np.mean([height for height in rect_arr[anchor_indexes, 3]]), 2)

        # Estimate the position of the 0 score box
        zero_pos = round(x_mean-10*anchor_width, 2)

        # TODO check if the indice locations are valid 
        cords_indice = get_valid_indice(
            areas = area_arr,
            cords_arr = cords_arr,
            anchor_data = (x_mean, anchor_cords[:, 1]),
            rect_arr = rect_arr
        )

        cords_indice = cords_indice[cords_arr[cords_indice][:, 0] > zero_pos]

        # draw_cords(image, cords_arr[cords_indice], index=1) 
        
        rows, rect_rows = divide_into_rows(anchor_cords[:, 1], cords_arr[cords_indice], rect_arr[cords_indice])    

        scores, flags = get_scores(
            cord_rows = rows,
            rect_rows = rect_rows,
            anchor_data = (x_mean, anchor_cords[:, 1]),
            TYPE = TYPE
        )

        check_scores(scores, flags)

        # Make all scores integers (No decimals)
        scores = [row.astype(int) for row in scores]

        return scores, flags, rows, rect_rows

    def __str__(self) -> str:
        return str(self.scores)