from typing import Any, Callable, Iterable, Iterator, Optional, TypeVar, Tuple

T = TypeVar("T")

KeyFn = Callable[[T], Any]


def zip_pairs(
        xs: Iterable[T],
        ys: Iterable[T],
        key: Optional[KeyFn] = None
) -> Iterator[Tuple[Optional[T], Optional[T]]]:
    if not key:
        key = lambda x: 0

    xs = list(reversed(sorted(xs, key=key)))
    ys = list(reversed(sorted(ys, key=key)))

    while xs or ys:
        if not xs:
            yield None, ys.pop()
            continue
        if not ys:
            yield xs.pop(), None
            continue

        x_key = key(xs[-1])
        y_key = key(ys[-1])
        yield (xs.pop() if x_key <= y_key else None,
               ys.pop() if y_key <= x_key else None)
