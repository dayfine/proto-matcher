# proto-matcher

Test matchers for Protobuffer in Python.

This is based on [MessageDifferencer](https://developers.google.com/protocol-buffers/docs/reference/cpp/google.protobuf.util.message_differencer) as well as the [EqualsProto](https://github.com/google/googletest/issues/1761) googletest matcher.

## API

This packages provides the following [PyHamcrest](https://github.com/hamcrest/PyHamcrest) matchers:

### `equals_proto`

```python
equals_proto(message: Union[Message, str])
```
Test the argument equals the given protobuf message.

### `approximately`

```python
approximately(proto_matcher: Matcher[Message],
              float_margin: Optional[float] = None,
              float_fraction: Optional[float] = None)
```
Test the argument equals the given protobuf message, while comparing any float field using approximation.

### `ignoring_field_paths`

```python
ignoring_field_paths(field_paths: Set[Tuple[str]],
                     matcher: _ProtoMatcher)
```
Test the argument equals the given protobuf message, while ignoring those fields specified in the field paths.


### `ignoring_repeated_field_ordering`

```python
ignoring_repeated_field_ordering(proto_matcher: Matcher[Message])
```
Test the argument equals the given protobuf message, ignoring the ordering of any repeated field.


### `partially`

```python
partially(proto_matcher: Matcher[Message])
```
Test the argument partially equals the given protobuf message, i.e. if a field is in the argument but not in the expected message, it's ignored in the comparsion.
