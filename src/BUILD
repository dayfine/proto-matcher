load("@rules_python//python:defs.bzl", "py_library")
load("@py_deps//:requirements.bzl", "requirement")

py_library(
    name = "matcher",
    srcs = ["matcher.py"],
    srcs_version = "PY3",
    deps = [
        requirement("protobuf"),
        requirement("pyhamcrest"),
    ],
)
