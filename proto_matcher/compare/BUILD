load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("@py_deps//:requirements.bzl", "requirement")

package(default_visibility = ["//proto_matcher:internal"])

py_library(
    name = "module",
    srcs = ["__init__.py"],
    srcs_version = "PY3",
    deps = [
        ":compare",
    ],
)

py_library(
    name = "compare",
    srcs = ["compare.py"],
    srcs_version = "PY3",
    deps = [
        ":iter_util",
        requirement("protobuf"),
    ],
)

py_test(
    name = "compare_test",
    srcs = ["compare_test.py"],
    srcs_version = "PY3",
    deps = [
        ":compare",
        "//proto_matcher/testdata:test_py_pb2",
        requirement("protobuf"),
    ],
)

py_library(
    name = "iter_util",
    srcs = ["iter_util.py"],
    srcs_version = "PY3",
    deps = [
        requirement("protobuf"),
    ],
)
