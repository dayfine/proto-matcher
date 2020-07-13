load("@rules_python//python:defs.bzl", "py_library", "py_test")

package(default_visibility = ["//proto_matcher:internal"])

package_group(
    name = "internal",
    packages = [
        "//proto_matcher/...",
    ],
)

py_library(
    name = "proto_matcher",
    srcs = ["__init__.py"],
    srcs_version = "PY3",
    visibility = ["//visibility:public"],
    deps = [
        "//proto_matcher/matcher",
    ],
)
