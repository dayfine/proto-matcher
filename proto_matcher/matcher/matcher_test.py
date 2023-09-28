import unittest

from hamcrest import *
from google.protobuf import text_format

from proto_matcher.matcher.matcher import equals_proto
from proto_matcher.matcher.matcher import approximately
from proto_matcher.matcher.matcher import ignoring_field_paths
from proto_matcher.matcher.matcher import ignoring_repeated_field_ordering
from proto_matcher.matcher.matcher import partially
from proto_matcher.compare import compare
from proto_matcher.testdata import test_pb2

_TEST_PROTO = """
bars {
    short_id: -123
    name: "a bar"
    size: 1
    notes: "hehe"
    notes: "123"
}
bars {
    long_id: 888899990000
    progress: 0.31415926
    checked: True
    notes: "photo"
}
baz {
    status: ERROR
}
mapping {
    key: 5
    value: "haha"
}
mapping {
    key: 10
    value: "hello world!"
}
"""


class ProtoCompareTest(unittest.TestCase):

    def assertProtoCompareToBe(self, result: compare.ProtoComparisonResult,
                               to_be: bool):
        self.assertEqual(result.is_equal, to_be, result.explanation)

    def _get_test_proto(self):
        return text_format.Parse(_TEST_PROTO, test_pb2.Foo())

    def test_basic_equality(self):
        expected = self._get_test_proto()
        assert_that(self._get_test_proto(), equals_proto(expected))

    def test_taking_expected_text_proto(self):
        assert_that(self._get_test_proto(), equals_proto(_TEST_PROTO))

    def test_basic_inequality(self):
        expected = self._get_test_proto()
        expected.baz.Clear()
        assert_that(self._get_test_proto(), not_(equals_proto(expected)))

    def test_repeated_field_inequality(self):
        expected = self._get_test_proto()
        expected.bars.add().progress = 0.1
        assert_that(self._get_test_proto(), not_(equals_proto(expected)))

    def test_map_field_inequality(self):
        expected = self._get_test_proto()
        expected.mapping[15] = 'luck'
        assert_that(self._get_test_proto(), not_(equals_proto(expected)))

    def test_basic_partial_equality(self):
        assert_that(self._get_test_proto(),
                    partially(equals_proto(_TEST_PROTO)))

    def test_partial_equality_test_extra_field(self):
        expected = self._get_test_proto()
        expected.baz.Clear()
        assert_that(self._get_test_proto(), partially(equals_proto(expected)))

    def test_basic_partial_inequality(self):
        expected = self._get_test_proto()
        expected.baz.status = test_pb2.Baz.OK
        assert_that(self._get_test_proto(),
                    not_(partially(equals_proto(expected))))

    def test_partial_inequality_missing_field(self):
        actual = self._get_test_proto()
        actual.baz.Clear()
        assert_that(actual, not_(partially(equals_proto(_TEST_PROTO))))

    def test_repeated_field_partial_inequality(self):
        expected = self._get_test_proto()
        expected.bars.add().progress = 0.1
        assert_that(self._get_test_proto(),
                    not_(partially(equals_proto(expected))))

    def test_aproximate_equality(self):
        actual = self._get_test_proto()
        assert_that(actual, approximately(equals_proto(_TEST_PROTO)))

    def test_aproximate_modified_equality(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        expected.bars[0].progress = 2.300005
        actual.bars[0].progress = 2.300006
        assert_that(actual, approximately(equals_proto(expected)))

    def test_aproximate_modified_equality_double(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        expected.bars[0].precision = 2.3 + 1.1e-15
        actual.bars[0].precision = 2.3 + 1.2e-15
        assert_that(actual, not_(equals_proto(expected)))
        assert_that(actual, approximately(equals_proto(expected)))

    def test_within_fraction_or_margin_float(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        expected.bars[0].progress = 100.0
        actual.bars[0].progress = 109.9
        assert_that(actual, not_(equals_proto(expected)))

        assert_that(actual,
                    approximately(equals_proto(expected), float_margin=10.0))
        assert_that(actual,
                    approximately(equals_proto(expected), float_fraction=0.2))
        assert_that(
            actual,
            not_(approximately(equals_proto(expected), float_fraction=0.01)))
        assert_that(
            actual,
            approximately(equals_proto(expected),
                          float_fraction=0.1,
                          float_margin=10.0))

    def test_oneof_inequality(self):
        expected = self._get_test_proto()
        expected.bars[0].long_id = expected.bars[0].short_id
        assert_that(self._get_test_proto(), not_(equals_proto(expected)))

    def test_compare_proto_ignoring_fields(self):
        # a: 1,      2,    3, 9, 4, 5, 7,   2
        # b:   9, 0, 2, 7, 3,    4, 5,   6, 2
        pass

    def test_ignore_field_single(self):
        expected = text_format.Parse('baz { status: ERROR }', test_pb2.Foo())
        actual = text_format.Parse('', test_pb2.Foo())
        assert_that(actual, not_(equals_proto(expected)))

        assert_that(actual,
                    ignoring_field_paths({('baz',)}, equals_proto(expected)))

    def test_ignore_field_repeated(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        del actual.bars[:]
        assert_that(actual, not_(equals_proto(expected)))

        assert_that(actual,
                    ignoring_field_paths({('bars',)}, equals_proto(expected)))

    def test_ignore_field_multiple(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        del actual.bars[:]
        actual.baz.status = test_pb2.Baz.OK

        assert_that(
            actual,
            not_(ignoring_field_paths({('baz',)}, equals_proto(expected))))
        assert_that(
            actual,
            not_(ignoring_field_paths({('bars',)}, equals_proto(expected))))
        assert_that(
            actual,
            ignoring_field_paths({('bars',), ('baz',)}, equals_proto(expected)))

    def test_ignore_field_nested(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        actual.bars[0].size = 2

        assert_that(actual, not_(equals_proto(expected)))

        assert_that(
            actual,
            ignoring_field_paths({('bars', 'size')}, equals_proto(expected)))

    def test_compare_proto_repeated_fields_ignoring_order(self):
        expected = self._get_test_proto()
        actual = self._get_test_proto()
        reversed_bars = actual.bars[::-1]
        del actual.bars[:]
        actual.bars.extend(reversed_bars)
        assert_that(actual, not_(equals_proto(expected)))

        assert_that(actual,
                    ignoring_repeated_field_ordering(equals_proto(expected)))

    def test_ignore_nested_field_with_ignore_repeated_field_order(self):
        expected = test_pb2.Foo()
        expected.bars.extend([
            test_pb2.Bar(
                short_id=1,
                name='first bar',
            ),
            test_pb2.Bar(
                short_id=2,
                name='second bar',
            ),
        ])
        actual = test_pb2.Foo()
        actual.bars.extend([
            test_pb2.Bar(
                long_id=20,
                name='second bar',
            ),
            test_pb2.Bar(
                long_id=10,
                name='first bar',
            ),
        ])

        assert_that(actual, not_(equals_proto(expected)))
        assert_that(
            actual,
            not_(ignoring_repeated_field_ordering(equals_proto(expected))))
        ignored_fields = {('bars', 'short_id'), ('bars', 'long_id')}
        assert_that(
            actual,
            not_(ignoring_field_paths(ignored_fields, equals_proto(expected))))
        assert_that(
            actual,
            ignoring_repeated_field_ordering(
                ignoring_field_paths(ignored_fields, equals_proto(expected))))
        assert_that(
            actual,
            ignoring_field_paths(
                ignored_fields,
                ignoring_repeated_field_ordering(equals_proto(expected))))


if __name__ == '__main__':
    unittest.main()
