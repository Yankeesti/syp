"""Generic strategy registry."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Generic, TypeVar

K = TypeVar("K")
S = TypeVar("S")


class StrategyNotFoundError(LookupError):
    """Raised when a strategy for the given key is not registered."""


@dataclass(slots=True)
class StrategyRegistry(Generic[K, S]):
    """Registry for strategies keyed by a lookup value."""

    _strategies: dict[K, S]

    @classmethod
    def from_strategies(
        cls,
        strategies: Iterable[S],
        key_getter: Callable[[S], K],
    ) -> "StrategyRegistry[K, S]":
        strategy_map: dict[K, S] = {}
        for strategy in strategies:
            key = key_getter(strategy)
            if key in strategy_map:
                raise ValueError(f"Duplicate strategy key: {key}")
            strategy_map[key] = strategy
        return cls(strategy_map)

    def get(self, key: K) -> S:
        try:
            return self._strategies[key]
        except KeyError as exc:
            raise StrategyNotFoundError(f"No strategy for key: {key}") from exc
