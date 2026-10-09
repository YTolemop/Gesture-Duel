from core.types import RawHandSample, FeatureResult

class StudentNormalizer:
    def transform(self, sample: RawHandSample, config: dict) -> FeatureResult:
        """Required TODO. Input: RawHandSample, hand_mode single/dual, mirror_left,
        feature_version. Convert normalized image x/y/z to same pixel scale,
        translate wrist(0) to origin, scale by distance wrist(0)-middle_mcp(9),
        reject scale <10px, optionally mirror relative left x. Do not rotate-align.
        Return finite float32 (63,) for configured single hand; dual is left63,
        right63,left-present,right-present (128,), missing slots zero-filled.
        No hands -> invalid with features=None. See docs/student_tasks.md.
        """
        raise NotImplementedError('請完成 student/normalization.py: StudentNormalizer.transform')
