workspace(name = "proto_matcher")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "com_google_protobuf",
    sha256 = "832c476bb442ca98a59c2291b8a504648d1c139b74acc15ef667a0e8f5e984e7",
    strip_prefix = "protobuf-3.11.3",
    urls = ["https://github.com/google/protobuf/archive/v3.11.3.zip"],
)

http_archive(
    name = "com_github_grpc_grpc",
    sha256 = "b0d3b876d85e4e4375aa211a52a33b7e8ca9f9d6d97a60c3c844070a700f0ea3",
    strip_prefix = "grpc-1.28.1",
    urls = ["https://github.com/grpc/grpc/archive/v1.28.1.zip"],
)

http_archive(
    name = "rules_proto",
    sha256 = "602e7161d9195e50246177e7c55b2f39950a9cf7366f74ed5f22fd45750cd208",
    strip_prefix = "rules_proto-97d8af4dc474595af3900dd85cb3a29ad28cc313",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_proto/archive/97d8af4dc474595af3900dd85cb3a29ad28cc313.tar.gz",
        "https://github.com/bazelbuild/rules_proto/archive/97d8af4dc474595af3900dd85cb3a29ad28cc313.tar.gz",
    ],
)

http_archive(
    name = "rules_python",
    sha256 = "d3e40ca3b7e00b72d2b1585e0b3396bcce50f0fc692e2b7c91d8b0dc471e3eaf",
    strip_prefix = "rules_python-748aa53d7701e71101dfd15d800e100f6ff8e5d1",
    urls = [
        "https://github.com/bazelbuild/rules_python/archive/748aa53d7701e71101dfd15d800e100f6ff8e5d1.zip",
    ],
)

rules_python_external_version = "0.1.5"

http_archive(
    name = "rules_python_external",
    sha256 = "bc655e6d402915944e014c3b2cad23d0a97b83a66cc22f20db09c9f8da2e2789",
    strip_prefix = "rules_python_external-{version}".format(version = rules_python_external_version),
    url = "https://github.com/dillon-giacoppo/rules_python_external/archive/v{version}.zip".format(version = rules_python_external_version),
)

# ================================================================
# Proto extensions
# ================================================================
load("@com_google_protobuf//:protobuf_deps.bzl", "protobuf_deps")

protobuf_deps()

load("@com_github_grpc_grpc//bazel:grpc_deps.bzl", "grpc_deps")

grpc_deps()

load(
    "@rules_proto//proto:repositories.bzl",
    "rules_proto_dependencies",
    "rules_proto_toolchains",
)

rules_proto_dependencies()

rules_proto_toolchains()

# ================================================================
# Python extensions
# ================================================================
load("@rules_python//python:repositories.bzl", "py_repositories")

py_repositories()

# Only needed if using the packaging rules.
load("@rules_python_external//:repositories.bzl", "rules_python_external_dependencies")

rules_python_external_dependencies()

load("@rules_python_external//:defs.bzl", "pip_install")

pip_install(
    name = "py_deps",
    requirements = "//:requirements.txt",
)
