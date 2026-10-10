"""Theme classifier: transparent rules, sharpened by a small model trained on reference tags.

RuleClassifier    - regex taxonomy only. No training data, fully explainable.
HybridClassifier  - TF-IDF + the rule hits as features, one logistic regression per
                    theme, trained on data/labels.csv (reviews read one by one and tagged against
                    the codebook; in this repo that reading was done with an AI model).
                    Falls back to the rules for any theme with too few examples.

Reference tags always win: if a review has been read and tagged, `themes_for`
returns that tag and never the classifier's guess. Correct a tag in labels.csv and
every number downstream follows.
"""
import re

from . import taxonomy as T

POSITIVE = re.compile(
    r"^\W*((very|so|really|its?|it'?s|is|a|the|this|app|overall|all)\s+)*"
    r"(good|nice|great|excellent|awesome|super|superb|best|amazing|love\w*|useful|helpful|user\s?friendly|fine)"
    r"(\s+(app|aap|application|service|experience|one|features?|so\s+far|keep\s+developing))*\W*$", re.I)


class RuleClassifier:
    name = "rules"

    def predict(self, texts):
        return [T.classify(t) for t in texts]


class HybridClassifier:
    name = "rules + model"
    MIN_EXAMPLES = 15
    THRESHOLD = 0.45

    def __init__(self):
        self.models = {}

    def _rule_matrix(self, texts):
        import numpy as np
        return np.array([[2.0 if rx.search(t) else 0.0 for _, _, _, rx in T.THEMES] for t in texts])

    def _features(self, texts, fit=False):
        from scipy.sparse import csr_matrix, hstack
        from sklearn.feature_extraction.text import TfidfVectorizer
        low = [t.lower() for t in texts]
        if fit:
            self.word = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
            self.char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True)
            parts = [self.word.fit_transform(low), self.char.fit_transform(low)]
        else:
            parts = [self.word.transform(low), self.char.transform(low)]
        return hstack(parts + [csr_matrix(self._rule_matrix(texts))]).tocsr()

    def fit(self, texts, label_sets):
        from sklearn.linear_model import LogisticRegression
        X = self._features(texts, fit=True)
        keys = sorted({k for s in label_sets for k in s})
        for k in keys:
            y = [1 if k in s else 0 for s in label_sets]
            if sum(y) >= self.MIN_EXAMPLES and k != "other":
                self.models[k] = LogisticRegression(C=8, class_weight="balanced", max_iter=2000).fit(X, y)
        return self

    def predict(self, texts):
        texts = list(texts)
        if not texts:
            return []
        X = self._features(texts)
        proba = {k: m.predict_proba(X)[:, 1] for k, m in self.models.items()}
        out = []
        for i, t in enumerate(texts):
            rule = T.classify(t)
            hits = [k for k, p in proba.items() if p[i] >= self.THRESHOLD]
            hits += [k for k in rule if k not in self.models and k not in ("generic", "other") and k not in hits]
            specific = [k for k in hits if k not in ("generic", "positive_text")]
            if specific:
                out.append(specific)
            elif "positive_text" in hits or POSITIVE.search(t or ""):
                out.append(["positive_text"])
            else:
                out.append(rule if rule[0] in ("generic", "other") else ["generic"])
        return out


def load_labels(rows):
    """rows: dicts with review_id and themes ('a;b'). Returns {review_id: [themes]}."""
    return {r["review_id"]: [t for t in r["themes"].split(";") if t] for r in rows if r.get("themes")}


def build(reviews, labels):
    """Train on every labelled review whose text we hold; fall back to rules if we can't."""
    pairs = [(r["text"], set(labels[r["review_id"]])) for r in reviews if r["review_id"] in labels and r["text"]]
    if len(pairs) < 200:
        return RuleClassifier()
    try:
        return HybridClassifier().fit([p[0] for p in pairs], [p[1] for p in pairs])
    except ImportError:
        return RuleClassifier()


def themes_for(reviews, labels, clf):
    """The reference tag if there is one, otherwise the classifier."""
    need = [r for r in reviews if r["review_id"] not in labels]
    pred = dict(zip((r["review_id"] for r in need), clf.predict([r["text"] for r in need])))
    return {r["review_id"]: labels.get(r["review_id"]) or pred[r["review_id"]] for r in reviews}


def cross_validate(reviews, labels, folds=5, seed=0):
    """Out-of-fold precision / recall per theme for both classifiers, against the reference tags."""
    import random
    pairs = [(r["text"], set(labels[r["review_id"]])) for r in reviews if r["review_id"] in labels and r["text"]]
    random.Random(seed).shuffle(pairs)
    res = {"rules": {}, "hybrid": {}}
    preds = {"rules": [None] * len(pairs), "hybrid": [None] * len(pairs)}
    for f in range(folds):
        test = [i for i in range(len(pairs)) if i % folds == f]
        train = [i for i in range(len(pairs)) if i % folds != f]
        hy = HybridClassifier().fit([pairs[i][0] for i in train], [pairs[i][1] for i in train])
        for name, clf in (("rules", RuleClassifier()), ("hybrid", hy)):
            for i, p in zip(test, clf.predict([pairs[i][0] for i in test])):
                preds[name][i] = set(p)
    keys = sorted({k for _, s in pairs for k in s})
    for name in preds:
        TP = FP = FN = 0
        for k in keys:
            tp = sum(1 for (_, g), p in zip(pairs, preds[name]) if k in g and k in p)
            fp = sum(1 for (_, g), p in zip(pairs, preds[name]) if k not in g and k in p)
            fn = sum(1 for (_, g), p in zip(pairs, preds[name]) if k in g and k not in p)
            res[name][k] = {"n": tp + fn, "precision": round(tp / (tp + fp), 3) if tp + fp else None,
                            "recall": round(tp / (tp + fn), 3) if tp + fn else None}
            TP, FP, FN = TP + tp, FP + fp, FN + fn
        res[name]["_micro"] = {"n": len(pairs), "precision": round(TP / (TP + FP), 3), "recall": round(TP / (TP + FN), 3),
                               "f1": round(2 * TP / (2 * TP + FP + FN), 3)}
    return res
