import unittest

from google.protobuf import text_format

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

    def test_proto_comparable(self):
        self.assertTrue(compare.proto_comparable(test_pb2.Foo(),
                                                 test_pb2.Foo()))
        self.assertFalse(
            compare.proto_comparable(test_pb2.Foo(), test_pb2.Bar()))
        self.assertFalse(
            compare.proto_comparable(test_pb2.Baz(), test_pb2.Bar()))

        foo1 = test_pb2.Foo()
        foo1.baz.status = test_pb2.Baz.OK
        foo2 = test_pb2.Foo()
        bar = test_pb2.Bar()
        bar.progress = 0.75
        foo2.bars.append(bar)
        self.assertTrue(compare.proto_comparable(foo1, foo1))
        self.assertTrue(compare.proto_comparable(foo1, foo2))
        self.assertFalse(compare.proto_comparable(foo1, bar))

    def test_basic_equality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        self.assertProtoCompareToBe(compare.proto_compare(actual, expected),
                                    True)

    def test_basic_inequality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        expected.baz.Clear()
        self.assertProtoCompareToBe(compare.proto_compare(actual, expected),
                                    False)

    def test_repeated_field_inequality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        expected.bars.add().progress = 0.1
        self.assertProtoCompareToBe(compare.proto_compare(actual, expected),
                                    False)

    def test_map_field_inequality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        expected.mapping[15] = 'luck'
        self.assertProtoCompareToBe(compare.proto_compare(actual, expected),
                                    False)

    def test_basic_partial_equality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        opts = compare.ProtoComparisonOptions(
            scope=compare.ProtoComparisonScope.PARTIAL)
        self.assertProtoCompareToBe(
            compare.proto_compare(actual, expected, opts=opts), True)

    def test_partial_equality_test_extra_field(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        expected.baz.Clear()

        opts = compare.ProtoComparisonOptions(
            scope=compare.ProtoComparisonScope.PARTIAL)
        self.assertProtoCompareToBe(
            compare.proto_compare(actual, expected, opts=opts), True)

    def test_basic_partial_inequality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        expected.baz.status = test_pb2.Baz.OK

        opts = compare.ProtoComparisonOptions(
            scope=compare.ProtoComparisonScope.PARTIAL)
        self.assertProtoCompareToBe(
            compare.proto_compare(actual, expected, opts=opts), False)

    def test_partial_inequality_missing_field(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual.baz.Clear()

        opts = compare.ProtoComparisonOptions(
            scope=compare.ProtoComparisonScope.PARTIAL)
        self.assertProtoCompareToBe(
            compare.proto_compare(actual, expected, opts=opts), False)

    def test_repeated_field_partial_inequality(self):
        expected = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        actual = text_format.Parse(_TEST_PROTO, test_pb2.Foo())
        expected.bars.add().progress = 0.1

        opts = compare.ProtoComparisonOptions(
            scope=compare.ProtoComparisonScope.PARTIAL)
        self.assertProtoCompareToBe(
            compare.proto_compare(actual, expected, opts=opts), False)

    def test_compare_proto_ignoring_fields(self):
        pass

    def test_compare_proto_ignoring_field_paths(self):
        pass

    def test_compare_proto_repeated_fields_ignoring_order(self):
        pass

    def test_compare_proto_float_fields_by_margin(self):
        pass

    def test_compare_proto_float_fields_by_fraction(self):
        pass


if __name__ == '__main__':
    unittest.main()
