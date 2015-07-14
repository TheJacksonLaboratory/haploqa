import itertools

import numpy as np
from scipy import linalg
import matplotlib.pyplot as plt
import matplotlib as mpl
import pylab

from sklearn import mixture

import haploqa.haploqa as hqa


def main():
    print('running query')
    probe_data_by_probeset = hqa.generate_probe_data_by_probeset()
    print('query done')
    i = 0
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

        color_iter = itertools.cycle(['r', 'g', 'b', 'c', 'm'])

        Y_ = best_model.predict(X)

        #do_plot = len(set(Y_)) > 1
        do_plot = True

        if do_plot:
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


if __name__ == '__main__':
    main()
