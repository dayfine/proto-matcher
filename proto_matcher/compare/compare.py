import collections
import dataclasses
import enum
import math
import itertools
import sys
from typing import Any, Iterable, List, Mapping, Optional, Set, Tuple

from google.protobuf import descriptor
from google.protobuf import message

_FieldDescriptor = descriptor.FieldDescriptor
_FLT_EPSILON = 1.19209e-07
_DBL_EPSILON = sys.float_info.epsilon


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
    ignore_field_paths: Optional[Set[Tuple[str]]] = None
    treating_nan_as_equal: bool = False
    float_comp: ProtoFloatComparison = ProtoFloatComparison.EXACT
    # |float_margin| and |float_fraction| are only used when
    # float_comp = APPROXIMATE.
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
        if not self._opts.ignore_field_paths:
            self._opts.ignore_field_paths = set()
        # should expand ignored field paths using desc...
        self._desc = desc

    def compare(
        self,
        expected: message.Message,
        actual: message.Message,
        field_path: Tuple[str] = ()
    ) -> ProtoComparisonResult:
        return _combine_results([
            self._compare_field(expected, actual, field_desc, field_path)
            for field_desc in actual.DESCRIPTOR.fields
        ])

    def _compare_field(self, expected: message.Message, actual: message.Message,
                       field_desc: _FieldDescriptor,
                       field_path: Tuple[str]) -> ProtoComparisonResult:
        field_path = field_path + (field_desc.name,)
        if field_path in self._opts.ignore_field_paths:
            return _equality_result()

        # Repeated field
        if field_desc.label == _FieldDescriptor.LABEL_REPEATED:
            expected_values = getattr(expected, field_desc.name)
            actual_values = getattr(actual, field_desc.name)
            # Map field
            if isinstance(expected_values, collections.abc.Mapping):
                return self._compare_map(expected_values, actual_values,
                                         field_path)
            return self._compare_repeated_field(expected_values, actual_values,
                                                field_desc, field_path)

        # Singular field
        if (self._opts.scope == ProtoComparisonScope.PARTIAL and
                not _is_field_set(expected, field_desc)):
            return _equality_result()

        return self._compare_value(getattr(expected, field_desc.name, None),
                                   getattr(actual, field_desc.name, None),
                                   field_desc, field_path)

    def _compare_repeated_field(
            self, expected_values: Iterable[Any], actual_values: Iterable[Any],
            field_desc: _FieldDescriptor,
            field_path: Tuple[str]) -> ProtoComparisonResult:
        if self._opts.repeated_field_comp == RepeatedFieldComparison.AS_SET:
            expected_values.sort()
            actual_values.sort()
        return _combine_results([
            self._compare_value(expected, actual, field_desc, field_path)
            for expected, actual in itertools.zip_longest(
                expected_values, actual_values)
        ])

    def _compare_map(self, expected_map: Mapping[Any, Any],
                     actual_map: Mapping[Any, Any],
                     field_path: Tuple[str]) -> ProtoComparisonResult:
        desc = expected_map.GetEntryClass().DESCRIPTOR
        key_desc = desc.fields_by_name['key']
        value_desc = desc.fields_by_name['value']

        return _combine_results([
            self._compare_key_value_pair(expected_kv, actual_kv, key_desc,
                                         value_desc, field_path)
            for expected_kv, actual_kv in itertools.zip_longest(
                sorted(expected_map.items()), sorted(actual_map.items()))
        ])

    def _compare_key_value_pair(
            self, expected_kv: Optional[Tuple[Any, Any]],
            actual_kv: Optional[Tuple[Any, Any]], key_desc: _FieldDescriptor,
            value_desc: _FieldDescriptor,
            field_path: Tuple[str]) -> ProtoComparisonResult:
        if not expected_kv or not actual_kv:
            return _inequality_result(
                _readable(expected_kv, value_desc, key_desc),
                _readable(actual_kv, value_desc, key_desc))
        expected_key, expected_value = expected_kv
        actual_key, actual_value = actual_kv
        return _combine_results([
            self._compare_value(expected_key, actual_key, key_desc, field_path),
            self._compare_value(expected_value, actual_value, value_desc,
                                field_path)
        ])

    def _compare_value(self, expected: Any, actual: Any,
                       field_desc: _FieldDescriptor, field_path: Tuple[str]):
        if _is_message(field_desc):
            if expected and actual:
                return self.compare(expected, actual, field_path)
            return _inequality_result(expected, actual, field_desc)

        if field_desc.cpp_type == _FieldDescriptor.CPPTYPE_DOUBLE:
            return self._compare_float(expected, actual, _DBL_EPSILON)
        if field_desc.cpp_type == _FieldDescriptor.CPPTYPE_FLOAT:
            return self._compare_float(expected, actual, _FLT_EPSILON)
        # Simple primitive value
        return _equality_result() if expected == actual else _inequality_result(
            expected, actual, field_desc)

    def _compare_float(self, expected: float, actual: float,
                       epsilon: float) -> ProtoComparisonResult:
        if expected == actual:
            return _equality_result()
        if (self._opts.treating_nan_as_equal and math.isnan(expected) and
                math.isnan(actual)):
            return _equality_result()

        if self._opts.float_comp == ProtoFloatComparison.EXACT:
            return _inequality_result(expected, actual)

        # float_comp == APPROXIMATE
        fraction = self._opts.float_fraction or 0.0
        margin = self._opts.float_margin or (32 * epsilon)
        is_equal = _within_fraction_or_margin(expected, actual, fraction,
                                              margin)
        return _equality_result() if is_equal \
            else _inequality_result(expected, actual)


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


def _inequality_result(
        expected: Any,
        actual: Any,
        field_desc: Optional[_FieldDescriptor] = None) -> ProtoComparisonResult:
    if field_desc:
        expected = _readable(expected, field_desc)
        actual = _readable(actual, field_desc)
    return ProtoComparisonResult(
        is_equal=False,
        explanation=f'Expected: {expected}; Actual: {actual}',
    )


def _readable(value: Any,
              value_desc: _FieldDescriptor,
              key_desc: Optional[_FieldDescriptor] = None) -> str:
    if key_desc and value:
        key, value = value
        return f'key: {_readable(key, key_desc)}' \
               f'value: {_readable(value, value_desc)}'
    if _is_enum_field(value_desc):
        return _get_enum_name(value, value_desc)
    return str(value)


def _get_enum_name(enum_value: int, field_desc: _FieldDescriptor) -> str:
    return field_desc.enum_type.values[enum_value].name


def _within_fraction_or_margin(x: float, y: float, fraction: float,
                               margin: float) -> bool:
    if not (fraction >= 0.0 and fraction < 1.0 and margin >= .0):
        raise ValueError(f'Invalid fraction {fraction} or margin {margin}')
    if math.isinf(x) or math.isinf(y):
        return False
    relative_margin = fraction * max(abs(x), abs(y))
    return abs(x - y) <= max(margin, relative_margin)
