import dataclasses
import enum
import itertools
from typing import Any, List, Optional

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
    is_equal: bool = True
    explanation: str = ''


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

    def __init__(self, opts: ProtoComparisonOptions,
                 desc: descriptor.Descriptor):
        self._opts = opts
        # should expand ignored field paths using desc...
        self._desc = desc

    def compare(self, expected: message.Message,
                actual: message.Message) -> ProtoComparisonResult:
        return _combine_results([
            self._compare_field(expected, actual, field_desc)
            for field_desc in actual.DESCRIPTOR.fields
        ])

    def _compare_field(self, expected: message.Message, actual: message.Message,
                       field_desc: _FieldDescriptor) -> ProtoComparisonResult:
        # Repeated field
        if field_desc.label == _FieldDescriptor.LABEL_REPEATED:
            return self._compare_repeated_field(
                getattr(expected, field_desc.name)[:],
                getattr(actual, field_desc.name)[:], field_desc)

        # Singular field
        if (self._opts.scope == ProtoComparisonScope.PARTIAL and
                not _is_field_set(expected, field_desc)):
            return _equality_result()

        return self._compare_value(getattr(expected, field_desc.name, None),
                                   getattr(actual, field_desc.name, None),
                                   field_desc)

    def _compare_repeated_field(
            self, expected_values: List[Any], actual_values: List[Any],
            field_desc: _FieldDescriptor) -> ProtoComparisonResult:
        if self._opts.repeated_field_comp == RepeatedFieldComparison.AS_SET:
            expected_values.sort()
            actual_values.sort()
        return _combine_results([
            self._compare_value(expected, actual, field_desc)
            for expected, actual in itertools.zip_longest(
                expected_values, actual_values)
        ])

    def _compare_value(self, expected: Any, actual: Any,
                       field_desc: _FieldDescriptor):
        if _is_message(field_desc):
            if expected and actual:
                return self.compare(expected, actual)
            return _inequality_result(expected, actual, field_desc)

        return _equality_result() if expected == actual else _inequality_result(
            expected, actual, field_desc)

    def _compare_float(self):
        pass


def _combine_results(
        results: List[ProtoComparisonResult]) -> ProtoComparisonResult:
    return ProtoComparisonResult(
        is_equal=all([res.is_equal for res in results]),
        explanation='\n'.join(
            [res.explanation for res in results if res.explanation]),
    )


def _is_message(field_desc: _FieldDescriptor) -> bool:
    return field_desc.cpp_type == _FieldDescriptor.CPPTYPE_MESSAGE


def _is_enum_field(field_desc: _FieldDescriptor) -> bool:
    return field_desc.enum_type is not None


def _is_field_set(msg: message.Message, field_desc: _FieldDescriptor) -> bool:
    if _is_message(field_desc):
        return msg.HasField(field_desc.name)
    if _is_enum_field(field_desc):
        return getattr(msg, field_desc.name) != 0
    return hasattr(msg, field_desc.name)


def _equality_result() -> ProtoComparisonResult:
    return ProtoComparisonResult()


def _inequality_result(expected: Any, actual: Any,
                       field_desc: _FieldDescriptor) -> ProtoComparisonResult:
    if _is_enum_field(field_desc):
        expected = _get_enum_name(expected, field_desc)
        actual = _get_enum_name(actual, field_desc)
    return ProtoComparisonResult(
        is_equal=False,
        explanation=f'Expected: {expected}; Actual: {actual}',
    )


def _get_enum_name(enum_value: int, field_desc: _FieldDescriptor) -> str:
    return field_desc.enum_type.values[enum_value].name
