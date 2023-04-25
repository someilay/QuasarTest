import numpy as np


def predict_activity(last_activities: list[int]) -> float:
    a_mat = np.ones((len(last_activities), 2))
    for i in range(len(last_activities)):
        a_mat[i][0] = i
    b_vec = np.linalg.pinv(a_mat).dot(np.array(last_activities))
    return np.array([len(last_activities), 1]).dot(b_vec)


def activity_prob(last_activities: list[int]) -> float:
    count = predict_activity(last_activities)

    prob = (count / last_activities[0]) if last_activities[0] else 1
    prob = 0 if prob < 0 else prob
    prob = 1 if prob > 1 else prob

    return prob
