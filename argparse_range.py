import argparse
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, TypeVar, Union

T = TypeVar("T", int, float)

def range_action(minimum: T, maximum: T, range_formatter: Callable=str):
    """Return an Action which will limit the input argument to be within the given range (inclusive)"""
    if not minimum < maximum:
        raise TypeError(f"minimum {minimum} must be less than maximum {maximum}")

    class RangeAction(argparse.Action):
        def __init__(
            self,
            option_strings: Sequence[str],
            dest: str,
            nargs: Union[int, str, None] = None,
            const: Union[T, None] = None,
            default: Union[T, str, None] = None,
            type: Union[
                Callable[[str], T], Callable[[str], T], argparse.FileType, None
            ] = None,
            choices: Optional[Iterable[T]] = None,
            required: bool = False,
            help: Optional[str] = None,
            metavar: Union[str, Tuple[str, ...], None] = None,
        ) -> None:
            self.range_formatter: Callable = range_formatter
            self.range_comment: str = f"(must be in range {range_formatter(minimum)}..={range_formatter(maximum)})"
            if isinstance(help, str):
                help = f"{help} {self.range_comment}"
            else:
                help = self.range_comment
            if isinstance(default, str) and type is None:
                raise RuntimeWarning(
                    f"RangeAction has default {default} with type {__builtins__.type(default)}, which may lead to inconsistent types in the returned Namespace"
                )
            super().__init__(
                option_strings,
                dest,
                nargs=nargs,
                const=const,
                default=default,
                type=type,
                choices=choices,
                required=required,
                help=help,
                metavar=metavar,
            )

        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Union[str, None] = None,
        ) -> None:
            def check_value(v):
                if not minimum <= v <= maximum:
                    raise argparse.ArgumentError(
                        argument=self,
                        message=f"Invalid choice: {self.range_formatter(v)} {self.range_comment}",
                    )

            converter: Callable[[str], T]
            if callable(self.type) and not isinstance(self.type, argparse.FileType):
                converter = self.type
            elif isinstance(minimum, int):
                converter = lambda s: int(s)
            elif isinstance(minimum, float):
                converter = lambda s: float(s)

            if isinstance(values, list):
                values = [converter(v) for v in values]
                for v in values:
                    check_value(v)
            elif isinstance(values, str):
                values = converter(values)
                check_value(values)
            elif values is None:
                pass  # User specified `nargs="?"`
            else:
                # User specified a `type`, and it was a single argument, and that conversion has already happened
                check_value(values)

            setattr(namespace, self.dest, values)

    return RangeAction