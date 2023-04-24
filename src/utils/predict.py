import numpy as np


def predict_activity(last_activities: list[int]) -> float:
    a_mat = np.ones((len(last_activities), 2))
    for i, val in enumerate(last_activities):
        a_mat[i][0] = val
    b_vec = np.linalg.pinv(a_mat).dot(np.array(last_activities))
    return np.array([len(last_activities), 1]).dot(b_vec)
