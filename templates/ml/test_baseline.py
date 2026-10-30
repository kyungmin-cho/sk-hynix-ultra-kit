import importlib.util
import random
import unittest
from unittest import mock

from . import baseline as bl
from . import metrics

HAS_SKLEARN = importlib.util.find_spec("sklearn") is not None


def _data(n=400, seed=11):
    rng = random.Random(seed)
    X, yc, yr = [], [], []
    for _ in range(n):
        a, b, c = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(5, 2)
        X.append([a, b if rng.random() > 0.05 else None, c])
        yc.append("NG" if 2 * a - b + rng.gauss(0, 0.5) > 1.0 else "OK")
        yr.append(3 * a + 0.5 * c + rng.gauss(0, 0.3))
    return X, yc, yr


class TestBaseline(unittest.TestCase):
    def _check_cls(self, prefer, kind):
        X, y, _ = _data()
        m = bl.fit_model(X[:300], y[:300], prefer=prefer)
        self.assertEqual(m.kind, kind)
        pred = m.predict(X[300:])
        acc = metrics.classification_metrics(y[300:], pred, positive="NG")["accuracy"]
        dacc = metrics.classification_metrics(y[300:], bl.dummy_model(y[:300]).predict(X[300:]), positive="NG")["accuracy"]
        self.assertGreater(acc, dacc + 0.05)
        self.assertEqual(m.classes, ["NG", "OK"])  # classes[1]=OK가 '양성 확률' 기준
        auc = metrics.roc_auc(y[300:], [1 - p for p in m.predict_proba(X[300:])], positive="NG")
        self.assertGreater(auc, 0.85)

    def _check_reg(self, prefer, kind):
        X, _, y = _data()
        m = bl.fit_model(X[:300], y[:300], task="regression", prefer=prefer)
        self.assertEqual(m.kind, kind)
        rmse = metrics.regression_metrics(y[300:], m.predict(X[300:]))["rmse"]
        drmse = metrics.regression_metrics(y[300:], bl.dummy_model(y[:300], "regression").predict(X[300:]))["rmse"]
        self.assertLess(rmse, drmse * 0.5)

    def test_stdlib_forced(self):  # sklearn이 있어도 폴백 경로를 항상 검사
        self._check_cls("stdlib", "stdlib-logistic")
        self._check_reg("stdlib", "stdlib-linear")

    def test_auto(self):
        kind = "sklearn-hgb" if HAS_SKLEARN else "stdlib-logistic"
        self._check_cls("auto", kind)

    @unittest.skipUnless(HAS_SKLEARN, "scikit-learn not installed (stdlib path tested above)")
    def test_sklearn_path(self):
        self._check_cls("sklearn", "sklearn-hgb")
        self._check_reg("sklearn", "sklearn-hgb")

    def test_sklearn_missing(self):  # sklearn이 없는 상황을 흉내 내 auto 폴백과 강제 실패를 확인
        with mock.patch.object(bl, "_sklearn", return_value=None):
            with self.assertRaises(ImportError):
                bl.fit_model([[1.0], [2.0]], [0, 1], prefer="sklearn")
            self.assertEqual(bl.fit_model([[1.0], [2.0]], [0, 1]).kind, "stdlib-logistic")

    def test_deterministic_and_errors(self):
        X, y, _ = _data(120)
        p1 = bl.fit_model(X, y, prefer="stdlib").predict_proba(X[:5])
        p2 = bl.fit_model(X, y, prefer="stdlib").predict_proba(X[:5])
        self.assertEqual(p1, p2)
        with self.assertRaises(ValueError):
            bl.fit_model([[1.0]] * 3, [0, 1, 2], prefer="stdlib")
        with self.assertRaises(ValueError):
            bl.fit_model([], [])


if __name__ == "__main__":
    unittest.main()
