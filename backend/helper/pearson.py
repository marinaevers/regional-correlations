import numpy as np
from joblib import Parallel, delayed
import multiprocessing

num_cores = multiprocessing.cpu_count()


def pearson_corr_distance_matrix(timelines, lag=0):
    if lag == 0:
        return np.corrcoef(timelines)

    def corr(timelines, timeline, lag):
        corr_mat = np.zeros((1, len(timelines)))
        for j, t in enumerate(timelines):
            t1 = timeline if lag == 0 else timeline[:-lag],
            t2 = t[lag:]
            corr_mat[0][j] = np.corrcoef(t1, t2)[0, 1]
        return corr_mat[0]

    results = Parallel(n_jobs=int(num_cores), verbose=10)(delayed(corr)(timelines, timeline, lag) for timeline in timelines)

    return np.array(results)
