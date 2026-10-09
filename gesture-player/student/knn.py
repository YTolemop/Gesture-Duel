from core.types import Prediction

class StudentKNN:
    def fit(self, features, labels, config: dict) -> None:
        """Required TODO. features finite float32 (N,D), labels (N,) classId 0..9.
        Store training data/settings; validate dimensions, N and k. Choose distance,
        deterministic ties and unknown rejection thresholds. No algorithm supplied.
        """
        raise NotImplementedError('請完成 student/knn.py: StudentKNN.fit')

    def predict(self, features) -> Prediction:
        """Required TODO. One finite float32 (D,) -> Prediction(label, valid,
        nearest_distance, vote_ratio). Choose neighbors, vote and rejection.
        Unknown must be NONE/invalid, not forcibly one of ten labels.
        """
        raise NotImplementedError('請完成 student/knn.py: StudentKNN.predict')
