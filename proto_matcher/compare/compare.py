import dataclasses
import enum
import itertools
from typing import List, Optional

from google.protobuf import descriptor
from google.protobuf import message

_FieldDescriptor = descriptor.FieldDescriptor


class RepeatedFieldComparison(enum.Enum):
    AS_LIST = enum.auto()
    AS_SET = enum.auto()


class ProtoComparisonScope(enum.Enum):
    FULL = enum.auto()
    PARTIAL = enum.auto()


class ProtoFloatComparison(enum.Enum):
    EXACT = enum.auto()
    APPROXIMATE = enum.auto()


@dataclasses.dataclass
class ProtoComparisonOptions:
    repeated_field_comp: RepeatedFieldComparison = RepeatedFieldComparison.AS_LIST
    scope: ProtoComparisonScope = ProtoComparisonScope.FULL
    ignore_fields: Optional[List[str]] = None
    ignore_field_paths: Optional[List[str]] = None
    treating_nan_as_equal: bool = False
    float_comp: ProtoFloatComparison = ProtoFloatComparison.EXACT
    # |float_margin| and |float_fraction| are only used when
    # float_comp = APPROXIMATE. Only one of them should be set.
    float_margin: Optional[float] = None
    float_fraction: Optional[float] = None


@dataclasses.dataclass
class ProtoComparisonResult:
    is_equal: bool
    explanation: str


def proto_compare(actual: message.Message,
                  expected: message.Message,
                  opts: ProtoComparisonOptions = None) -> ProtoComparisonResult:
    if not proto_comparable(actual, expected):
        return ProtoComparisonResult(
            is_equal=False,
            explanation=
            f'Expected message of type: {expected.DESCRIPTOR.full_name}.'
            f'Actual: {actual.DESCRIPTOR.full_name}',
        )

    if not opts:
        opts = ProtoComparisonOptions()

    differencer = MessageDifferencer(opts, actual.DESCRIPTOR)
    # It's important for 'expected' to be the first argument here, as
    # compare() is not symmetric.  When we do a partial comparison,
    # only fields present in the first argument of compare() are
    # considered.
    return differencer.compare(expected, actual)


def proto_comparable(actual: message.Message,
                     expected: message.Message) -> bool:
    return actual.DESCRIPTOR == expected.DESCRIPTOR


class MessageDifferencer():

    def __init__(self,
                 opts: ProtoComparisonOptions,
                 desc: descriptor.Descriptor,
                 explain: bool = False):
        self._opts = opts
        # should expand ignored field paths using desc...
        self._desc = desc
        self._explain = explain

    def compare(self, a: message.Message,
                b: message.Message) -> ProtoComparisonResult:
        # TODO: Full vs. Partial
        # Right now this is partial?
        return _combine_results([
            self._compare_field(b, field_desc, field_value)
            for field_desc, field_value in a.ListFields()
        ])

    def _compare_field(self, other: message.Message,
                       field_desc: _FieldDescriptor,
                       field_value) -> ProtoComparisonResult:
        field_name = field_desc.name
        if not b.HasField(field_name):
            return ProtoComparisonResult(
                is_equal=False,
                explanation=f'|{field_name}| expected but not set',
            )

        other_value = getattr(b, field_name)
        if field_desc.label == _FieldDescriptor.LABEL_REPEATED:
            return self._compare_repeated_field(field_value[:], other_value[:])
        return self._compare_singular_field(field_value, other_value,
                                            field_desc)

    def _compare_repeated_field(a: List, b: List) -> ProtoComparisonResult:
        if self._opts.repeated_field_comp == RepeatedFieldComparison.AS_SET:
            other_values.sort()
            values.sort()
        return _combine_results([
            self._compare_value(a, b)
            for a, b in itertools.zip_longest(values, other_values)
        ])

    def _compare_singular_field(
            self, a, b, field_desc: _FieldDescriptor) -> ProtoComparisonResult:
        if field_desc.cpp_type == _FieldDescriptor.CPPTYPE_MESSAGE:
            return self.compare(a, b)

        return ProtoComparisonResult(
            is_equal=a == b,
            explanation='',
        )

    def _compare_value(self):
        pass

    def _compare_float(self):
        pass


def _combine_results(
        results: List[ProtoComparisonResult]) -> ProtoComparisonResult:
    return ProtoComparisonResult(
        is_equal=all([res.is_equal for res in results]),
        explanation='\n'.join(
            [res.explanation for res in results if res.explanation]),
    )
