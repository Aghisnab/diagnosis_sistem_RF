# custom_transformer.py

class FeatureSelector:
    def __init__(self, features):
        self.features = features

    def transform(self, X):
        return X[self.features]

    def fit(self, X, y=None):
        return self
