import unittest

from google.protobuf import text_format

from proto_matcher.compare import compare
from proto_matcher.testdata import test_pb2


class ProtoCompareTest(unittest.TestCase):

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

    def test_compare_protos(self):
        foo1 = test_pb2.Foo()
        self.assertTrue(compare.proto_compare(foo1, foo1).is_equal)
        foo2 = test_pb2.Foo()
        self.assertTrue(compare.proto_compare(foo1, foo2).is_equal)

        textpb = """
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
        """
        foo = text_format.Parse(textpb, test_pb2.Foo())
        another = text_format.Parse(textpb, test_pb2.Foo())
        self.assertTrue(compare.proto_compare(foo, another).is_equal)

        copied = test_pb2.Foo()
        copied.CopyFrom(foo)
        self.assertTrue(compare.proto_compare(foo, copied).is_equal)

    def test_compare_partial_protos(self):
        pass

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
