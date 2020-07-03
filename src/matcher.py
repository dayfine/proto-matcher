import dataclasses
import enum

from hamcrest.core.base_matcher import BaseMatcher


class _RepeatedFieldComparison(enum.Enum):
    AS_LIST = enum.auto()
    AS_SET = enum.auto()


class _ProtoComparisonScope(enum.Enum):
    FULL = enum.auto()
    PARTIAL = enum.auto()


class _ProtoFloatComparison(enum.Enum):
    EXACT = enum.auto()
    APPROXIMATE = enum.auto()


@dataclasses.dataclass
class _ProtoComparison:
    repeated_field_comp: _RepeatedFieldComparison = _RepeatedFieldComparison.AS_LIST
    scope: _ProtoComparisonScope = _ProtoComparisonScope.FULL
    ignore_fields: List[str]
    ignore_field_paths: List[str]
    treating_nan_as_equal: bool = False
    float_comp: _ProtoFloatComparison = _ProtoFloatComparison.EXACT
    has_custom_margin: bool = False  # only used when float_comp = APPROXIMATE
    has_custom_fraction: bool = False  # only used when float_comp = APPROXIMATE
    float_margin: float  # only used when has_custom_margin is true
    float_fraction: float  # only used when has_custom_fraction is true


def proto_comparable() -> bool:
  return False

def _EqualsProto(BaseMatcher):
    pass


def _IgnoringFields(BaseMatcher):
    pass


def _IgnoringFieldPaths(BaseMatcher):
    pass


def _IgnoringRepeatedFieldOrdering(BaseMatcher):
    pass


def _Partially(BaseMatcher):
    pass
