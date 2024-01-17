import numpy as np


def find_close_groups(arr, tolerance, index:int = 0, exclude_singles:bool = True):
    '''
    Find groups within given arr where integer values fall within the tolerance
    '''
    # Sort the array
    sorted_arr = arr[np.argsort(arr[:, index])]

    # Find the differences between consecutive elements
    diffs = np.diff(sorted_arr, axis=0)

    # Find the indices where the differences are greater than the tolerance
    break_indices = np.where(diffs[:, index] > tolerance)[0]

    # Split the array into subarrays based on the break indices
    subarrays = np.split(sorted_arr, break_indices + 1)

    min_size = 1 if exclude_singles is True else 0

    # Filter out subarrays with only one element (no close neighbors)
    close_groups = [subarr for subarr in subarrays if len(subarr) > min_size]

    return close_groups


def remove_outliers(data: np.ndarray, ret_inliers: bool = False):
    '''
    Removes outliers outside of quartile 1 and 3
    '''
    Q1 = np.percentile(data, 25)
    Q3 = np.percentile(data, 75)

    IQR = Q3 - Q1

    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q1 + 1.5 * IQR

    inliers = ((data > lower_bound) | (data < upper_bound))

    valid_values = data[inliers]

    if ret_inliers:
        return inliers

    return valid_values


def format_indice(ind1, ind2):
    ind_c = np.column_stack((ind1, ind2))

    ret_indice = []

    for tup in ind_c:
        ret_indice.append(tup[0] and tup[1])

    return ret_indice


def adjusted_is_close(a:int, b:int) -> bool:
    # Relative tolerance is default value
    rtol = 1.e-5

    # Compute 10% of smaller value for absolute tolerance
    atol = 0.1 * min(a, b) 

    is_close = np.isclose(a, b, rtol, atol)

    return is_close


def arr_adj_is_close(arr, b:int, not_bool:bool = False):
    indice = []
    
    for a in arr:
        val = not adjusted_is_close(a, b) if not_bool else adjusted_is_close(a, b)

        indice.append(val)

    return indice


def find_valid_diff(arr, ret_indice:bool=False):
    # Sort array
    sorted_arr = np.sort(arr)

    # Find differences
    differences = np.diff(sorted_arr)

    indices = []

    for i, diff in enumerate(differences):
        if i >= len(differences)-1:
            continue

        is_close = adjusted_is_close(diff, differences[i+1])

        indices.append(is_close)

    # Append final value to indices as array is shortened by 2 when processed
    indices = np.append(indices, [indices[-1], indices[-1]])

    # Get valid differences and then computer mean | differences is 1 shorter than sorted_arr
    diff = differences[indices[:-1]].mean()

    # TODO find if there is a missing value inbetween

    if ret_indice:
        return diff, indices

    return diff


def filter_cords(min_y, max_y, arrs = None, arrays:bool = False):
    if not arrays:
        return arrs[(arrs[:, 1] > min_y) & (arrs[:, 1] < max_y)]

    ret_arr = []

    for arr in arrs:
        np_arr = np.array(arr)

        ret_arr.append(np_arr[(np_arr[:, 1] > min_y) & (np_arr[:, 1] < max_y)])

    return ret_arr


def get_valid_cords(cord_arrs, arrays:bool = False):
    if not arrays:
        cord_arrs = [cord_arrs] 

    all_valid_cords = []


    def process_cords(cords):
        cords = np.array(cords)
        valid_cords = np.full(len(cords), True, dtype=bool) 

        vectorized_comparison = np.vectorize(adjusted_is_close) 
        mask = vectorized_comparison(cords[:-1, 1], cords[1:, 1])

        valid_cords[:-1][mask] = False
        valid_cords[-1] = True

        return valid_cords


    all_valid_cords = [process_cords(cords) for cords in cord_arrs]

    if not arrays:
        return all_valid_cords[0]

    return all_valid_cords


def reshape_2d(arr):
    # length of array
    n = arr.size
    
    # N-D array N dimension
    N = int(round(n/2, 0))
    
    # calculating M
    M = n//N

    return np.reshape(arr, (N, M))


def get_anchor_pos(cords_arr, image_height):
    '''
    Finds the largest mean x val across potential anchor groups
    Anchor groups being a group of closely related area size with a len between 5 and 10

    Returns largest mean value found

    countours : list of contours generated by
        cv2.findContours(thresh_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cords_arr : list of cordinates generated by
        #.approxPolyDP(contour, epsilon, True)
        cv2.boundingRect contour is from contours
        epsilon = 0.01 * cv2.arcLength(contour, True)
        approx = cv2(approx)
    '''

    potential_cords = find_close_groups(cords_arr, 10)

    filtered_length = [cords for cords in potential_cords if len(cords) < 50 and len(cords) > 5]

    inlier_cords = []

    for arr in filtered_length:
        sorted_arr = arr[np.argsort(arr[:, 0])]

        indice_x = remove_outliers(sorted_arr, ret_inliers = True)

        sorted_2d = reshape_2d(sorted_arr[indice_x])

        sorted_inliers = sorted_2d[np.argsort(sorted_2d[:, 1])]

        indice_y = remove_outliers(sorted_inliers, ret_inliers = True)

        inlier_cords.append(reshape_2d(sorted_inliers[indice_y]))

    inlier_cords, arrays_bool = (inlier_cords, True) if len(inlier_cords) > 1 else (np.array(inlier_cords[0]), False)

    min_y = round(image_height * 0.05)
    max_y = round(image_height - min_y)

    filtered_cords = filter_cords(min_y, max_y, inlier_cords, arrays_bool)

    valid_cords = get_valid_cords(filtered_cords, arrays_bool)

    if arrays_bool:
        anchor_diffs = [np.diff(filtered_cords[i][valid, 1]).mean() for i, valid in enumerate(valid_cords)]
        index = np.argsort(anchor_diffs)[-1]

        cords = filtered_cords[index]
        valid = valid_cords[index]

        anchor_cords = cords[valid]
        x_mean = np.round(anchor_cords[:, 0].mean(), 2)

    else:
        anchor_cords = filtered_cords[valid_cords]
        x_mean = np.round(filtered_cords[:, 0].mean(), 2)

    _, anchor_indice = find_valid_diff(anchor_cords[:, 1], ret_indice=True)

    anchor_cords = anchor_cords[anchor_indice]

    return anchor_cords, x_mean 