import itertools
import math

import numpy as np
from scipy import linalg
from scipy.stats import norm
import matplotlib.pyplot as plt
import matplotlib as mpl
import pylab

from sklearn import mixture
from sklearn.cluster import DBSCAN

import haploqa.haploqa as hqa


def cluster_gmm():
    probe_data_by_probeset = hqa.generate_probe_data_by_probeset()
    for i, probeset_data_for_all_samples in enumerate(probe_data_by_probeset):
        print(probeset_data_for_all_samples['probeset_id'])
        probe_data = probeset_data_for_all_samples['probe_data']
        norm_a_vals = [float('nan') if x['probe_a_norm'] is None else x['probe_a_norm'] for x in probe_data]
        norm_b_vals = [float('nan') if x['probe_b_norm'] is None else x['probe_b_norm'] for x in probe_data]

        X = np.transpose([norm_a_vals, norm_b_vals])

        # remove any non-finite values
        x_finite = np.isfinite(X)
        X = X[np.all(x_finite, axis=1), ]

        print('finding model')
        lowest_info_crit = None
        best_model = None
        best_n_components = 0
        cv_types = ['tied'] #['spherical', 'tied', 'diag', 'full']
        for cv_type in cv_types:
            print(cv_type)
            for n_components in range(1, 6):
                model = mixture.GMM(n_components=n_components, covariance_type=cv_type, n_iter=100)

                model.fit(X)
                info_crit = model.bic(X)
                print('Probe ID: {}, # Clusts: {}, BIC: {}'.format(
                    probeset_data_for_all_samples['probeset_id'],
                    n_components,
                    info_crit
                ))
                if lowest_info_crit is None or info_crit < lowest_info_crit:
                    best_model = model
                    lowest_info_crit = info_crit
                    best_n_components = n_components
                    best_cv_type = cv_type

        print('found best n_components: {}, cv_type: {}'.format(best_n_components, best_cv_type))

        Y_ = best_model.predict(X)

        #do_plot = len(set(Y_)) > 1
        do_plot = False
        if do_plot:
            color_iter = itertools.cycle(['r', 'g', 'b', 'c', 'm'])

            fig = pylab.figure()
            ax = fig.add_subplot(111, aspect='equal')

            for j, (mean, covar, color) in enumerate(zip(best_model.means_, best_model._get_covars(), color_iter)):
                v, w = linalg.eigh(covar)
                u = w[0] / linalg.norm(w[0])

                # as the DP will not use every component it has access to
                # unless it needs it, we shouldn't plot the redundant
                # components.
                if not np.any(Y_ == j):
                    continue

                if do_plot:
                    ax.scatter(X[Y_ == j, 0], X[Y_ == j, 1], .8, color=color)

                    # Plot an ellipse to show the Gaussian component
                    angle = np.arctan(u[1] / u[0])
                    angle = 180 * angle / np.pi  # convert to degrees
                    ell = mpl.patches.Ellipse(mean, v[0], v[1], 180 + angle, color=color)
                    ell.set_clip_box(ax.bbox)
                    ell.set_alpha(0.5)
                    ax.add_artist(ell)

            fig.suptitle('Probe ID: {}, # Clusts: {}, BIC: {}'.format(
                probeset_data_for_all_samples['probeset_id'],
                best_n_components,
                lowest_info_crit
            ))
            # pylab.show()
            fig.savefig(
                'imgout/{}-best.png'.format(probeset_data_for_all_samples['probeset_id']),
                bbox_inches='tight'
            )
            plt.clf()


def test_cluster_DBSCAN():
    probe_data_by_probeset = hqa.generate_probe_data_by_probeset()
    for i, probeset_data_for_all_samples in enumerate(probe_data_by_probeset):
        print(probeset_data_for_all_samples['probeset_id'])
        probe_data = probeset_data_for_all_samples['probe_data']
        norm_a_vals = [float('nan') if x['probe_a_norm'] is None else x['probe_a_norm'] for x in probe_data]
        norm_b_vals = [float('nan') if x['probe_b_norm'] is None else x['probe_b_norm'] for x in probe_data]

        X = np.transpose([norm_a_vals, norm_b_vals])

        # remove any non-finite values
        x_finite = np.isfinite(X)
        X = X[np.all(x_finite, axis=1), ]

        # NOTE: 0.075 seems to give the best result
        fig = pylab.figure()
        for i, eps in enumerate((0.1, 0.075, 0.05, 0.025)):
            db = DBSCAN(eps=eps, min_samples=5).fit(X)

            clust_label_set = set(db.labels_)
            color_iter = itertools.cycle(['r', 'g', 'b', 'c', 'm'])
            label_colors = dict(zip(clust_label_set - {-1}, color_iter))
            label_colors[-1] = 'k'

            n_clusters = len(clust_label_set - {-1})
            ax = fig.add_subplot(2, 2, i + 1, aspect='equal')
            ax.set_title('eps={}, # clusts={}'.format(eps, n_clusters))
            ax.scatter(X[:, 0], X[:, 1], .8, color=[label_colors[lbl] for lbl in db.labels_])

        fig.suptitle('DBSCAN Cluster {}'.format(probeset_data_for_all_samples['probeset_id']))
        # pylab.show()
        fig.savefig(
            'imgout/{}.png'.format(probeset_data_for_all_samples['probeset_id']),
            bbox_inches='tight'
        )
        plt.close('all')


def inverse_rot(x, y):
    '''
    Returns a 2D rotation matrix which will invert thetas rotation
    :param theta: the rotation angle to invert
    :return: the rotation matrix which will inverse thetas rotation
    '''

    # a 2D rotation matrix looks like:
    #
    # R = | cos(theta), -sin(theta) |
    #     | sin(theta), cos(theta)  |
    #
    # in order to invert the rotation we can just transpose the matrix giving
    #
    # R = |  cos(theta), sin(theta) |
    #     | -sin(theta), cos(theta) |

    hyp = math.sqrt(x * x + y * y)
    if hyp == 0:
        return np.array([
            [0.0, 0.0],
            [0.0, 0.0],
        ])
    else:
        cos_theta = x / hyp
        sin_theta = y / hyp
        return np.array([
            [cos_theta,  sin_theta],
            [-sin_theta, cos_theta],
        ])


def cluster_DBSCAN():
    probe_data_by_probeset = hqa.generate_probe_data_by_probeset()
    for i, probeset_data_for_all_samples in enumerate(probe_data_by_probeset):
        probeset_id = probeset_data_for_all_samples['probeset_id']
        probe_data = probeset_data_for_all_samples['probe_data']
        norm_a_vals = [float('nan') if x['probe_a_norm'] is None else x['probe_a_norm'] for x in probe_data]
        norm_b_vals = [float('nan') if x['probe_b_norm'] is None else x['probe_b_norm'] for x in probe_data]

        X = np.transpose([norm_a_vals, norm_b_vals])

        # remove any non-finite values
        X = X[np.all(np.isfinite(X), axis=1), ]

        # cluster points with DBSCAN algorithm (from all that I have tried this seems to be fairly fast
        # and gives better clusters than the others)
        # TODO eps and min_samples should not be hard coded. Move them to a config file (or maybe adjust
        #      based on number of samples
        eps = 0.075
        db = DBSCAN(eps=eps, min_samples=5).fit(X)
        label_set = {lbl for lbl in db.labels_ if lbl != -1}

        print('{} # clusters: {}'.format(probeset_id, len(label_set)))

        do_plot = False
        if do_plot:
            fig = pylab.figure()
            color_iter = itertools.cycle(['r', 'g', 'b', 'c', 'm'])
            label_colors = dict(zip(label_set, color_iter))
            label_colors[-1] = 'k'

            ax = fig.add_subplot(111, aspect='equal')
            ax.set_title('{} eps={}, # clusts={}'.format(probeset_id, eps, len(label_set)))
            ax.scatter(X[:, 0], X[:, 1], .8, color=[label_colors[lbl] for lbl in db.labels_])
            max_range = np.max(X)
            ax.set_xlim([0, max_range])
            ax.set_ylim([0, max_range])

        for cluster_label in label_set:
            clust_points = X[db.labels_ == cluster_label, :]
            clust_points_t = np.transpose(clust_points)
            clust_mean = np.mean(clust_points, 0)
            mean_x, mean_y = clust_mean

            # we need a rotation matrix for each cluster mean
            clust_rot_mat = inverse_rot(mean_x, mean_y)
            rotated_cluster_points = clust_rot_mat.dot(clust_points_t)

            rot_x_var, rot_y_var = np.var(rotated_cluster_points, 1)

            if do_plot:
                theta = math.atan(mean_y / mean_x)
                theta_deg = 180 * theta / math.pi
                ellipse = mpl.patches.Ellipse(
                    np.array([mean_x, mean_y]),
                    math.sqrt(rot_x_var) * 6, math.sqrt(rot_y_var) * 6,
                    theta_deg,
                    color=label_colors[cluster_label]
                )
                ellipse.set_alpha(0.3)
                ax.add_artist(ellipse)

        if do_plot:
            fig.savefig(
                'imgout/{}.png'.format(probeset_data_for_all_samples['probeset_id']),
                bbox_inches='tight'
            )
            plt.close('all')


def main():
    cluster_DBSCAN()


if __name__ == '__main__':
    main()
