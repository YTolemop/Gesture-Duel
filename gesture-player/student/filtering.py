from core.types import Prediction

class StudentFilter:
    def update(self, prediction: Prediction, timestamp: float) -> str:
        """Optional TODO. Monotonic local seconds, never assumed FPS. Return fixed
        label or NONE. Stabilize and switch using your chosen history policy.
        Shared no-hand/error safety still overrides this result.
        """
        raise NotImplementedError('選用濾波請完成 student/filtering.py: StudentFilter.update')

    def reset(self) -> None:
        """Optional TODO. Clear all history on reconnect, model/config change."""
        raise NotImplementedError('選用濾波請完成 student/filtering.py: StudentFilter.reset')
