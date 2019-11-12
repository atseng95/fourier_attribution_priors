import numpy as np
import sklearn.metrics
import scipy.stats
import scipy.spatial.distance
import profile_performance
from datetime import datetime
import warnings

def test_vectorized_corr_mse_1():
    np.random.seed(20191110)
    num_corrs, corr_len = 500, 1000
    arr1 = np.random.randint(100, size=(num_corrs, corr_len))
    arr2 = np.random.randint(100, size=(num_corrs, corr_len))

    print("Testing Pearson correlation...")
    pears_scipy = np.empty(num_corrs)
    a = datetime.now()
    for i in range(num_corrs):
        pears_scipy[i] = scipy.stats.pearsonr(arr1[i], arr2[i])[0]
    b = datetime.now()
    print("\tTime to compute (Scipy): %ds" % (b - a).seconds)

    a = datetime.now()
    pears_vect = profile_performance.pearson_corr(arr1, arr2) 
    b = datetime.now()
    print("\tTime to compute (vectorized): %ds" % (b - a).seconds)
    print("\tSame result? %s" % np.allclose(pears_vect, pears_scipy))

    print("Testing Spearman correlation...")
    spear_scipy = np.empty(num_corrs)
    a = datetime.now()
    for i in range(num_corrs):
        spear_scipy[i] = scipy.stats.spearmanr(arr1[i], arr2[i])[0]
    b = datetime.now()
    print("\tTime to compute (Scipy): %ds" % (b - a).seconds)

    a = datetime.now()
    spear_vect = profile_performance.spearman_corr(arr1, arr2) 
    b = datetime.now()
    print("\tTime to compute (vectorized): %ds" % (b - a).seconds)
    print("\tSame result? %s" % np.allclose(spear_vect, spear_scipy))


def test_vectorized_corr_mse_2():
    np.random.seed(20191110)
    num_samples, num_tasks, profile_len = 500, 4, 1000
    bin_sizes = [1, 4, 10]
    arr1 = np.random.randint(100, size=(num_samples, num_tasks, profile_len, 2))
    arr2 = np.random.randint(100, size=(num_samples, num_tasks, profile_len, 2))
    arr3 = np.random.randint(100, size=(num_samples, num_tasks, 2))
    arr4 = np.random.randint(100, size=(num_samples, num_tasks, 2))

    print("Testing binned correlation and MSE...")
    a = datetime.now()
    # Combine the profile length and strand dimensions (i.e. pool strands)
    new_shape = (num_samples, num_tasks, -1)
    arr1_flat = np.reshape(arr1, new_shape)
    arr2_flat = np.reshape(arr2, new_shape)
    pears_scipy = np.empty((num_samples, num_tasks, len(bin_sizes)))
    spear_scipy = np.empty((num_samples, num_tasks, len(bin_sizes)))
    mse_scipy = np.empty((num_samples, num_tasks, len(bin_sizes)))
    for i in range(num_samples):
        for j in range(num_tasks):
            slice1, slice2 = arr1_flat[i, j], arr2_flat[i, j]
            for k, bin_size in enumerate(bin_sizes):
                # Bin the values, taking the maximum for each bin
                bins1 = profile_performance.bin_array_max(slice1, bin_size)
                bins2 = profile_performance.bin_array_max(slice2, bin_size)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    # Ignore warnings when computing correlations using sklearn,
                    # to avoid warnings when input is constant
                    pears_scipy[i, j, k] = scipy.stats.pearsonr(bins1, bins2)[0]
                    spear_scipy[i, j, k] = scipy.stats.spearmanr(
                        bins1, bins2
                    )[0]
                    mse_scipy[i, j, k] = sklearn.metrics.mean_squared_error(
                        bins1, bins2
                    )
    b = datetime.now()
    print("\tTime to compute (SciPy): %ds" % (b - a).seconds)
    
    a = datetime.now()
    pears_vec, spear_vec, mse_vec = profile_performance.binned_count_corr_mse(
        arr1, arr2, bin_sizes
    )
    b = datetime.now()
    print("\tTime to compute (vectorized): %ds" % (b - a).seconds)

    print("\tSame Pearson result? %s" % np.allclose(pears_vec, pears_scipy))
    print("\tSame Spearman result? %s" % np.allclose(spear_vec, spear_scipy))
    print("\tSame MSE result? %s" % np.allclose(mse_vec, mse_scipy))

    print("Testing total correlation and MSE...")
    a = datetime.now()
    # Reshape inputs to be T x N * 2 (i.e. pool samples and strands)
    arr3_swap = np.reshape(np.swapaxes(arr3, 0, 1), (num_tasks, -1))
    arr4_swap = np.reshape(np.swapaxes(arr4, 0, 1), (num_tasks, -1))

    # For each task, compute the correlations/MSE
    pears_scipy = np.empty(num_tasks)
    spear_scipy = np.empty(num_tasks)
    mse_scipy = np.empty(num_tasks)
    for j in range(num_tasks):
        arr3_list, arr4_list = arr3_swap[j], arr4_swap[j]
        pears_scipy[j] = scipy.stats.pearsonr(arr3_list, arr4_list)[0]
        spear_scipy[j] = scipy.stats.spearmanr(arr3_list, arr4_list)[0]
        mse_scipy[j] = sklearn.metrics.mean_squared_error(arr3_list, arr4_list)
    b = datetime.now()
    print("\tTime to compute (SciPy): %ds" % (b - a).seconds)
    
    a = datetime.now()
    pears_vec, spear_vec, mse_vec = profile_performance.total_count_corr_mse(
        arr3, arr4
    )
    b = datetime.now()
    print("\tTime to compute (vectorized): %ds" % (b - a).seconds)

    print("\tSame Pearson result? %s" % np.allclose(pears_vec, pears_scipy))
    print("\tSame Spearman result? %s" % np.allclose(spear_vec, spear_scipy))
    print("\tSame MSE result? %s" % np.allclose(mse_vec, mse_scipy))


def test_vectorized_auprc():
    np.random.seed(20191110)
    num_vecs, vec_len = 5000, 1000
    input_size = (num_vecs, vec_len)
    true_vals = []
    pred_vals = np.random.randint(5, size=input_size) / 10
    pred_vals = np.concatenate([pred_vals] * 4)
    # Normal inputs
    true_vals.append(np.random.randint(2, size=input_size))
    # Include some -1
    true_vals.append(np.random.randint(2, size=input_size))
    rand_mask = np.random.randint(2, size=input_size).astype(bool)
    true_vals[1][rand_mask] = -1
    # All positives
    true_vals.append(np.ones_like(true_vals[0]))
    # All negatives
    true_vals.append(np.zeros_like(true_vals[0]))
    true_vals = np.concatenate(true_vals)

    print("Testing auPRC...")
    auprc_scipy = np.empty(pred_vals.shape[0])
    a = datetime.now()
    for i in range(pred_vals.shape[0]):
        t, p = true_vals[i], pred_vals[i]
        mask = (t == 0) | (t == 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Ignore warnings when computing auPRC with sklearn, to avoid
            # warnings when there are no true positives
            auprc_scipy[i] = sklearn.metrics.average_precision_score(
                t[mask], p[mask]
            )
    b = datetime.now()
    print("\tTime to compute (Sklearn): %ds" % (b - a).seconds)

    a = datetime.now()
    auprc_vec = profile_performance.auprc_score(true_vals, pred_vals)
    b = datetime.now()
    print("\tTime to compute (vectorized): %ds" % (b - a).seconds)

    auprc_scipy = np.nan_to_num(auprc_scipy)
    auprc_vec = np.nan_to_num(auprc_vec)

    print("\tSame result? %s" % np.allclose(auprc_scipy, auprc_vec))


def test_vectorized_jsd():
    np.random.seed(20191110)
    num_vecs, vec_len = 500, 1000
    input_size = (num_vecs, vec_len)
    arr1 = np.random.random(input_size)
    arr2 = np.random.random(input_size)
    # Make some rows 0
    arr1[-1] = 0
    arr2[-1] = 0
    arr1[-2] = 0
    arr2[-3] = 0

    print("Testing JSD...")
    jsd_scipy = np.empty(num_vecs)
    a = datetime.now()
    for i in range(num_vecs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Ignore warnings when computing JSD with scipy, to avoid
            # warnings when there are no true positives
            jsd_scipy[i] = scipy.spatial.distance.jensenshannon(
                arr1[i], arr2[i]
            )
    jsd_scipy = np.square(jsd_scipy)
    b = datetime.now()
    print("\tTime to compute (SciPy): %ds" % (b - a).seconds)

    a = datetime.now()
    jsd_vec = profile_performance.jensen_shannon_distance(arr1, arr2)
    b = datetime.now()
    print("\tTime to compute (vectorized): %ds" % (b - a).seconds)

    jsd_scipy = np.nan_to_num(jsd_scipy)
    jsd_vec = np.nan_to_num(jsd_vec)

    print("\tSame result? %s" % np.allclose(jsd_scipy, jsd_vec))


if __name__ == "__main__":
    # test_vectorized_jsd()
    # test_vectorized_corr_mse_1()
    # test_vectorized_corr_mse_2()
    test_vectorized_auprc()