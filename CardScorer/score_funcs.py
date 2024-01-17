import numpy as np

from CardScorer.contour_funcs import remove_outliers, arr_adj_is_close, adjusted_is_close, find_close_groups


def estimate_scores(arr, width, ten_pos):
    '''
    Estimates scores based on the difference in x values between the cords divided by the width
    '''
    
    # Make the array right to left 10 -> 0
    sorted_group = np.flip(np.sort(arr[:, 0]))

    diffs = np.diff(sorted_group)

    def round_diffs(arr):
        decimals, _ = np.modf(arr)

        round_mask = np.where(decimals < -0.95)

        arr[round_mask] -= 1

        adj_diffs = np.trunc(arr)

        return adj_diffs

    adj_diffs = round_diffs(diffs/width)

    # Estimated scores
    est_scores = np.zeros(len(sorted_group))

    if np.isclose(sorted_group[0], ten_pos):
        est_scores[0] = 10

    else:
        # Estimate number of squares away from 10
        est_diff = np.trunc((ten_pos - sorted_group[0]) / width)

        est_score = 10 - est_diff

        est_scores[0] = est_score

    for i, val in enumerate(adj_diffs):
        # Estimate score based on previous estimated score
        est_score = est_scores[i] + val

        est_scores[i+1] = est_score

    return est_scores


def format_indice(ind1, ind2):
    ind_c = np.column_stack((ind1, ind2))

    ret_indice = []

    for tup in ind_c:
        ret_indice.append(tup[0] and tup[1])

    return ret_indice


def remove_outliers_2d(arr):
    '''
    Takes a 2d array and reuturns an indice removing any outliers in either column.
    '''

    # Seperate x and y cordinates into seperate NDarrays
    x_vals = arr[:, 0]
    y_vals = arr[:, 1]

    # Remove outliers from both NDarrays
    valid_x = remove_outliers(x_vals, ret_inliers = True)
    valid_y = remove_outliers(y_vals, ret_inliers = True)

    # Make the indice a 1d array comapring both bools when staked as columns
    valid_indice = format_indice(valid_x, valid_y)

    return valid_indice


def get_valid_indice(areas, cords_arr, anchor_data, rect_arr):
    # Seperate anchor_data for readability
    anchor_pos, anchor_cords = anchor_data
    
    anchor_indice = np.array([], dtype=np.int64)

    # Find indexes where anchor_y_cord matches in cords_arr
    for y_val in anchor_cords:
        anchor_indice = np.append(anchor_indice, np.where(cords_arr[:, 1] == y_val))

    # Find mean area of anchor contours
    area = np.mean(areas[anchor_indice])

    # Find indices where areas are valid
    areas_indice = np.where((areas > 0.2 * area)
                               & (areas < area - area * 0.1))

    # Get cordinates for contours
    outliers_indice = remove_outliers_2d(cords_arr[areas_indice])

    new_indice = areas_indice[0][outliers_indice]

    # Estimate mind and max y values
    anchor_indice = [np.where(cords_arr == cords)[0][0] for cords in anchor_cords]

    anchor_rects = rect_arr[anchor_indice]

    mean_height = round(anchor_rects[:, 3].mean(), 2)

    # Estimate min and max values for image
    min_y = round(anchor_rects[:, 1].min() - mean_height * 2.5) # Min has to be shorter because of the card
    max_y = round(anchor_rects[:, 1].max() + mean_height * 3) # Max has to be longet

    is_close_indice = arr_adj_is_close(cords_arr[new_indice][:, 0], anchor_pos, not_bool = True)

    # Remove any values greater than or close to anchor_pos
    x_indice = np.where(cords_arr[new_indice][is_close_indice][:, 0] < anchor_pos)

    x_indice = new_indice[is_close_indice][x_indice]

    max_y_indice = np.where(cords_arr[x_indice][:, 1] < max_y)
    min_y_indice = np.where(cords_arr[x_indice][max_y_indice][:, 1] > min_y)


    return x_indice[max_y_indice][min_y_indice]


def find_closest_avg_index(arr, target_value, window_size):
    if len(arr) < window_size:
        raise ValueError(f"Window size is larger than given arr {len(arr)} < {len(window_size)}")

    # Create a rolling window view of the list
    # Allows for calculating average within window
    window = np.convolve(arr, np.ones(window_size, dtype=int), 'same')

    rolling_averges = np.convolve(arr, np.ones(window_size, dtype=int), 'same') / window_size

    # Calculate the average for each window and find index where average is closest to target value
    closest_index = np.argmin(np.abs(rolling_averges - target_value))

    start = closest_index - round(window_size/2)
    end = closest_index + round(window_size/2+0.5)

    return (start, end)


def get_scores(cord_rows, rect_rows, anchor_data, TYPE:int = 0):
    '''
    Returns:
    est_scores - scores estimated from data given
    flags : list[list[int]] - Flags of each row, 0 - Valid, 1 - Potentially Invalid, 2 - Invalid
    '''
    # Seperate anchor_data for readability
    anchor_pos, anchor_cords = anchor_data

    avg_widths = []

    for i, rect_row in enumerate(rect_rows):
        if TYPE == 1 and i > 0:
            break

        rects = np.array([rect[0] for rect in rect_row])
        avg_widths.append(rects[:, 2].mean())

    # Estimation of where the 10 box is 
    BASELINE = np.abs(anchor_pos - (np.mean(avg_widths) * 2.75))

    estimated_scores = []

    # Flags on each row, 0 - Valid, 1 - Potentially Invalid, 2 - Invalid
    flags = []

    for i, row in enumerate(cord_rows):
        if TYPE == 1 and i > 0:
            break

        width = avg_widths[i]

        group = np.full(shape = (5), fill_value = None)
        group_flag = np.zeros((5))

        for i, cords in enumerate(row):
            if len(cords) > 1:
                group_flag[i] = 2

            group[i] = cords[0]

        # Remove invalid rows 
        valid_group = np.vstack(group[np.where(group_flag == 0)])

        est_scores = estimate_scores(
            arr = valid_group,
            width = width,
            ten_pos = BASELINE 
        )

        group_flag[np.where(est_scores < 0)] = 1

        flags.append(group_flag)

        estimated_scores.append(est_scores)

    return estimated_scores, flags


def check_scores(scores, flags):
    '''
    For adjusting scores if they go below 0
    '''

    # Get index of potentially invalid rows
    pot_invalid_index = [
        i for i, group_flags in enumerate(flags) 
        if 1 in group_flags
    ]

    for i in pot_invalid_index:
        cur_scores = scores[i]

        offset = abs(cur_scores[-1])

        adj_scores = cur_scores + offset

        scores[i] = adj_scores


def divide_into_rows(anchor_cords, cords, rect_arr):
    # Find rows of cords to condense them into one for finding the 5 rows to each anchor
    close_groups = find_close_groups(cords, 10, index = 1, exclude_singles = False)

    rect_groups = []

    # get rect arr rows as well
    for i, group in enumerate(close_groups):

        rect_row = [rect_arr[i + i2] for i2, _ in enumerate(group)]

        rect_groups.append(rect_row)

    row_cords = [arr[0, 1] for arr in close_groups]

    rect_rows = []
    rows = []

    for anchr_y in anchor_cords:
        start, end = find_closest_avg_index(row_cords, anchr_y, 5)

        rows.append(close_groups[start:end])
        rect_rows.append(rect_groups[start:end])

    return rows, rect_rows