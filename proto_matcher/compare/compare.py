import collections
import copy
import dataclasses
import enum
import math
import sys
from typing import Any, Generic, Iterable, List, Mapping, Optional, Set, TypeVar, Tuple

from google.protobuf import descriptor
from google.protobuf import message

from proto_matcher.compare import iter_util

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


T = TypeVar("T")


@dataclasses.dataclass
class ProtoFieldComparisonArgs(Generic[T]):
    expected: T
    actual: T
    field_desc: _FieldDescriptor
    field_path: Tuple[str]


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
            self._compare(
                ProtoFieldComparisonArgs(expected=expected,
                                         actual=actual,
                                         field_desc=None,
                                         field_path=field_path))
        ])

    def _compare(
        self, args: ProtoFieldComparisonArgs[message.Message]
    ) -> ProtoComparisonResult:
        return _combine_results([
            self._compare_field(
                ProtoFieldComparisonArgs(expected=args.expected,
                                         actual=args.actual,
                                         field_desc=field_desc,
                                         field_path=args.field_path))
            for field_desc in args.actual.DESCRIPTOR.fields
        ])

    def _compare_field(
            self, args: ProtoFieldComparisonArgs[Any]) -> ProtoComparisonResult:
        cmp_args = copy.copy(args)
        field_name = cmp_args.field_desc.name
        cmp_args.field_path = cmp_args.field_path + (field_name,)
        if cmp_args.field_path in self._opts.ignore_field_paths:
            return _equality_result()

        cmp_args.expected = getattr(cmp_args.expected, field_name, None)
        cmp_args.actual = getattr(cmp_args.actual, field_name, None)

        # Repeated field
        if cmp_args.field_desc.label == _FieldDescriptor.LABEL_REPEATED:
            # Map field
            if isinstance(cmp_args.expected, collections.abc.Mapping):
                return self._compare_map(cmp_args)
            return self._compare_repeated_field(cmp_args)

        # Singular field
        if (self._opts.scope == ProtoComparisonScope.PARTIAL and
                not _is_field_set(cmp_args.expected, cmp_args.field_desc)):
            return _equality_result()

        return self._compare_value(cmp_args)

    def _compare_repeated_field(
            self, cmp_args: ProtoFieldComparisonArgs[Iterable]
    ) -> ProtoComparisonResult:
        # Copy first to avoid modifying the original inputs.
        expected_list = list(cmp_args.expected)
        actual_list = list(cmp_args.actual)
        if self._opts.repeated_field_comp == RepeatedFieldComparison.AS_SET:
            # Identify as many matches as possible to minimize the number of
            # reported diffs.
            for expected in list(expected_list):
                for actual in list(actual_list):
                    item_result = self._compare_value(
                        ProtoFieldComparisonArgs(expected=expected,
                                                 actual=actual,
                                                 field_desc=cmp_args.field_desc,
                                                 field_path=cmp_args.field_path))
                    if item_result.is_equal:
                        actual_list.remove(actual)
                        expected_list.remove(expected)
                        break
            # If diffs remain, best-effort sort the lists to minimize the number
            # of diffs between each element.
            # (This is only best-effort because it fails to overlook ignored
            # fields.)
            as_set_key = lambda x: str(x)
            expected_list.sort(key=as_set_key)
            actual_list.sort(key=as_set_key)

        return _combine_results([
            self._compare_value(
                ProtoFieldComparisonArgs(expected=expected,
                                         actual=actual,
                                         field_desc=cmp_args.field_desc,
                                         field_path=cmp_args.field_path))
            for expected, actual in iter_util.zip_pairs(expected_list,
                                                        actual_list)
        ])

    def _compare_map(
            self, cmp_args: ProtoFieldComparisonArgs[Mapping]
    ) -> ProtoComparisonResult:
        desc = cmp_args.expected.GetEntryClass().DESCRIPTOR
        key_desc = desc.fields_by_name['key']
        value_desc = desc.fields_by_name['value']

        return _combine_results([
            _combine_results([
                self._compare_value(
                    ProtoFieldComparisonArgs(expected=expected_kv and
                                             expected_kv[0],
                                             actual=actual_kv and actual_kv[0],
                                             field_desc=key_desc,
                                             field_path=cmp_args.field_path)),
                self._compare_value(
                    ProtoFieldComparisonArgs(expected=expected_kv and
                                             expected_kv[1],
                                             actual=actual_kv and actual_kv[1],
                                             field_desc=value_desc,
                                             field_path=cmp_args.field_path))
            ]) for expected_kv, actual_kv in iter_util.zip_pairs(
                cmp_args.expected.items(),
                cmp_args.actual.items(),
                key=lambda kv: kv[0])
        ])

    def _compare_value(self, cmp_args: ProtoFieldComparisonArgs[Any]):
        if _is_message(cmp_args.field_desc):
            if cmp_args.expected and cmp_args.actual:
                return self._compare(cmp_args)
            return _inequality_result(cmp_args)
        if _is_float(cmp_args.field_desc):
            return self._compare_float(cmp_args)
        return _equality_result() if cmp_args.expected == cmp_args.actual \
            else _inequality_result(cmp_args)

    def _compare_float(
            self, cmp_args: ProtoFieldComparisonArgs) -> ProtoComparisonResult:
        if cmp_args.expected == cmp_args.actual:
            return _equality_result()
        if (self._opts.treating_nan_as_equal and math.isnan(expected) and
                math.isnan(actual)):
            return _equality_result()

        if self._opts.float_comp == ProtoFloatComparison.EXACT:
            return _inequality_result(cmp_args)

        # float_comp == APPROXIMATE
        fraction = self._opts.float_fraction or 0.0
        margin = self._opts.float_margin or _get_float_comparison_epsilon(
            cmp_args.field_desc)
        is_equal = _within_fraction_or_margin(cmp_args.expected,
                                              cmp_args.actual, fraction, margin)
        return _equality_result() if is_equal else _inequality_result(cmp_args)


def _combine_results(
        results: List[ProtoComparisonResult]) -> ProtoComparisonResult:
    return ProtoComparisonResult(
        is_equal=all([res.is_equal for res in results]),
        explanation='\n'.join(
            [res.explanation for res in results if res.explanation]),
    )


def _is_message(field_desc: _FieldDescriptor) -> bool:
    return field_desc.cpp_type == _FieldDescriptor.CPPTYPE_MESSAGE


def _is_float(field_desc: _FieldDescriptor) -> bool:
    return field_desc.cpp_type in (_FieldDescriptor.CPPTYPE_DOUBLE,
                                   _FieldDescriptor.CPPTYPE_FLOAT)


def _is_enum(field_desc: _FieldDescriptor) -> bool:
    return field_desc.enum_type is not None


def _is_field_set(value: Any, field_desc: _FieldDescriptor) -> bool:
    if _is_enum(field_desc):
        return value != 0
    return bool(value)


def _equality_result() -> ProtoComparisonResult:
    return ProtoComparisonResult()


def _inequality_result(
        cmp_args: ProtoFieldComparisonArgs) -> ProtoComparisonResult:
    return ProtoComparisonResult(
        is_equal=False,
        explanation=_explain_diff(cmp_args),
    )


def _explain_diff(cmp_args: ProtoFieldComparisonArgs):
    expected = _readable(cmp_args.expected, cmp_args.field_desc)
    actual = _readable(cmp_args.actual, cmp_args.field_desc)
    # TODO: add index here.
    field_path_with_index = '.'.join(cmp_args.field_path)
    if expected and not actual:
        return f'deleted: {field_path_with_index}: {expected}\n'
    if actual and not expected:
        return f'added: {field_path_with_index}: {actual}\n'
    return f'modified: {field_path_with_index}: {expected} -> {actual}\n'


def _readable(value: Any,
              value_desc: _FieldDescriptor,
              key_desc: Optional[_FieldDescriptor] = None) -> str:
    if key_desc and value:
        key, value = value
        return f'key: {_readable(key, key_desc)}' \
               f'value: {_readable(value, value_desc)}'
    if _is_enum(value_desc):
        return _get_enum_name(value, value_desc)
    if type(value) == str:
        return f'\"{value}\"'
    return str(value)


def _get_enum_name(enum_value: int, field_desc: _FieldDescriptor) -> str:
    return field_desc.enum_type.values[enum_value].name


def _get_float_comparison_epsilon(field_desc: _FieldDescriptor):
    if field_desc.cpp_type == _FieldDescriptor.CPPTYPE_DOUBLE:
        return _DBL_EPSILON * 32
    if field_desc.cpp_type == _FieldDescriptor.CPPTYPE_FLOAT:
        return _FLT_EPSILON * 32
    raise TypeError('Float comparison called on non-float types')


def _within_fraction_or_margin(x: float, y: float, fraction: float,
                               margin: float) -> bool:
    if not (fraction >= 0.0 and fraction < 1.0 and margin >= .0):
        raise ValueError(f'Invalid fraction {fraction} or margin {margin}')
    if math.isinf(x) or math.isinf(y):
        return False
    relative_margin = fraction * max(abs(x), abs(y))
    return abs(x - y) <= max(margin, relative_margin)
