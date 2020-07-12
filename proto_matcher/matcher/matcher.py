from typing import Optional, Set, Tuple, Union

from google.protobuf import message
from google.protobuf import text_format
from hamcrest.core.base_matcher import BaseMatcher
from hamcrest.core.description import Description
from hamcrest.core.helpers.wrap_matcher import wrap_matcher
from hamcrest.core.matcher import Matcher

from proto_matcher.compare import proto_compare, ProtoComparisonOptions
from proto_matcher.compare import ProtoComparisonScope
from proto_matcher.compare import ProtoFloatComparison
from proto_matcher.compare import RepeatedFieldComparison

_ProtoValue = Union[str, message.Message]

_ProtoMatcher = BaseMatcher[message.Message]


class _EqualsProto(_ProtoMatcher):

    def __init__(self, msg: _ProtoValue):
        self._msg = msg
        self._opts = ProtoComparisonOptions()

    def mut_options(self) -> ProtoComparisonOptions:
        return self._opts

    def matches(self,
                item: message.Message,
                mismatch_description: Optional[Description] = None) -> bool:
        expected = self._msg
        if isinstance(self._msg, str):
            proto_type = type(item)
            expected = text_format.Parse(self._msg, proto_type())
        cmp_result = proto_compare(item, expected, opts=self._opts)
        if not cmp_result.is_equal and mismatch_description:
            mismatch_description.append_text(cmp_result.explanation)
        return cmp_result.is_equal

    def describe_mismatch(self, item: message.Message,
                          mismatch_description: Description):
        self.matches(item, mismatch_description)

    def describe_to(self, description: Description):
        description.append_text(f"a protobuf of:\n{self._msg}")


def equals_proto(expected: message.Message) -> _ProtoMatcher:
    return _EqualsProto(expected)


def partially(matcher: _ProtoMatcher) -> _ProtoMatcher:
    matcher.mut_options().scope = ProtoComparisonScope.PARTIAL
    return matcher


def approximately(matcher: _ProtoMatcher,
                  float_margin: Optional[float] = None,
                  float_fraction: Optional[float] = None) -> _ProtoMatcher:
    opts = matcher.mut_options()
    opts.float_comp = ProtoFloatComparison.APPROXIMATE
    if float_margin:
        opts.float_margin = float_margin
    if float_fraction:
        opts.float_fraction = float_fraction
    return matcher


def ignoring_field_paths(field_paths: Set[Tuple[str]],
                         matcher: _ProtoMatcher) -> _ProtoMatcher:
    opts = matcher.mut_options()
    opts.ignore_field_paths = field_paths
    return matcher


def ignoring_repeated_field_ordering(matcher: _ProtoMatcher) -> _ProtoMatcher:
    opts = matcher.mut_options()
    opts.repeated_field_comp = RepeatedFieldComparison.AS_SET
    return matcher
