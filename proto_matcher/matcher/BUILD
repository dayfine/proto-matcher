load("@rules_python//python:defs.bzl", "py_library", "py_test")
load("@py_deps//:requirements.bzl", "requirement")

package(default_visibility = ["//proto_matcher:internal"])

py_library(
    name = "matcher",
    srcs = ["matcher.py"],
    srcs_version = "PY3",
    deps = [
        "//proto_matcher/compare:module",
        requirement("protobuf"),
        requirement("pyhamcrest"),
    ],
)

py_test(
    name = "matcher_test",
    srcs = ["matcher_test.py"],
    srcs_version = "PY3",
    deps = [
        ":matcher",
        "//proto_matcher/testdata:test_py_pb2",
        requirement("protobuf"),
        requirement("pyhamcrest"),
    ],
)
