"""Out-of-domain gate: Mahalanobis distance in a branch's feature space flags input unlike its training data.
The app runs it in 'warn' mode (scores unchanged); 'withhold' failed its pre-set rule (ledger O1)."""
import numpy as np
from sklearn.covariance import LedoitWolf


class MahalanobisGate:
    def __init__(self, kind='pooled', percentile=97.5):
        if kind not in ('pooled', 'class'):
            raise ValueError(f'unknown gate kind {kind!r}')
        self.kind = kind
        self.percentile = float(percentile)
        self.threshold_ = None

    def fit(self, X, y=None):
        X = np.asarray(X, dtype=np.float64)
        self.mean_ = X.mean(axis=0)
        self.scale_ = X.std(axis=0) + 1e-6
        Z = (X - self.mean_) / self.scale_
        if self.kind == 'pooled':
            centers = [Z.mean(axis=0)]
            resid = Z - centers[0]
        else:
            if y is None:
                raise ValueError("kind='class' needs labels")
            y = np.asarray(y)
            centers, parts = [], []
            for c in np.unique(y):
                m = Z[y == c].mean(axis=0)
                centers.append(m)
                parts.append(Z[y == c] - m)
            resid = np.vstack(parts)
        lw = LedoitWolf(assume_centered=True).fit(resid)
        self.precision_ = lw.precision_.astype(np.float32)
        self.centers_ = np.asarray(centers, dtype=np.float32)
        self.shrinkage_ = float(lw.shrinkage_)
        self.n_fit_ = int(len(X))
        return self

    def distance(self, X):
        """Mahalanobis distance (not squared) of each row to the nearest centre."""
        Z = ((np.atleast_2d(np.asarray(X, dtype=np.float64)) - self.mean_) / self.scale_).astype(np.float32)
        best = None
        for c in self.centers_:
            D = Z - c
            d2 = np.einsum('ij,jk,ik->i', D, self.precision_, D)
            best = d2 if best is None else np.minimum(best, d2)
        return np.sqrt(np.maximum(best, 0.0))

    def calibrate(self, X_in_domain):
        d = self.distance(X_in_domain)
        self.threshold_ = float(np.percentile(d, self.percentile))
        self.n_calibration_ = int(len(d))
        return self

    def is_out_of_domain(self, distance):
        if self.threshold_ is None:
            raise RuntimeError('gate not calibrated')
        return np.asarray(distance) > self.threshold_


def clip_video_distance(gate, crop_features):
    """A clip's video distance: the MEDIAN over its face crops, so one odd crop (blur, profile view) cannot flag a clip."""
    return float(np.median(gate.distance(np.asarray(crop_features))))
