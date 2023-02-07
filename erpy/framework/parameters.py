from __future__ import annotations

import abc
from typing import Iterable, List, Optional, T

import numpy as np


class Parameter(metaclass=abc.ABCMeta):
    def __init__(self, value: T) -> None:
        self._value = value

    @property
    @abc.abstractmethod
    def value(self) -> T:
        raise NotImplementedError

    def __eq__(self, other: Parameter) -> bool:
        eq = self.value == other.value
        if isinstance(eq, Iterable):
            eq = all(eq)
        return eq

    @value.setter
    def value(self, value) -> None:
        self._value = value

    def set_random_value(self) -> None:
        raise NotImplementedError


class FixedParameter(Parameter):
    def __init__(self, value: T) -> None:
        super().__init__(value)

    @property
    def value(self) -> T:
        return self._value

    def __eq__(self, other: Parameter) -> bool:
        eq = self.value == other.value
        if isinstance(eq, Iterable):
            eq = all(eq)
        return eq

    @value.setter
    def value(self, value) -> None:
        raise TypeError("Cannot change the value of a FixedParameter.")


class SynchronizedParameter(FixedParameter):
    def __init__(self, linked_parameter: Parameter) -> None:
        super().__init__(linked_parameter.value)
        self._linked_parameter = linked_parameter

    @property
    def value(self) -> T:
        return self._linked_parameter.value

    def __eq__(self, other: Parameter) -> bool:
        eq = self.value == other.value
        if isinstance(eq, Iterable):
            eq = all(eq)
        return eq

    @value.setter
    def value(self, value) -> None:
        raise TypeError("Cannot set the value of a SynchronizedParameter directly.")


class ContinuousParameter(Parameter):
    def __init__(self, low: float = -1.0, high: float = 1.0, value: Optional[float] = None) -> None:
        super(ContinuousParameter, self).__init__(value=value)
        self.low = low
        self.high = high

    @property
    def value(self) -> float:
        if self._value is None:
            self.set_random_value()

        self._value = np.clip(self._value, self.low, self.high)
        return self._value

    @value.setter
    def value(self, value) -> None:
        self._value = value

    def set_random_value(self) -> None:
        self._value = np.random.uniform(low=self.low, high=self.high)


class RangeParameter(Parameter):
    def __init__(self, low: float = -1.0, high: float = 1.0, value: Optional[np.ndarray] = None) -> None:
        super(RangeParameter, self).__init__(value)
        self.low = low
        self.high = high
        self.sorted = sorted

    @property
    def value(self) -> np.ndarray:
        if self._value is None:
            self.set_random_value()

        self._value = self._value.clip(self.low, self.high)
        self._value = sorted(np.array(self._value))

        return self._value

    @value.setter
    def value(self, value) -> None:
        assert self.low <= self.value <= self.high, f"[RangeParameter] Given value '{value}' is " \
                                                    f"not in range [{self.low}, {self.high}]"
        self._value = value

    def set_random_value(self) -> None:
        self._value = np.random.uniform(low=self.low, high=self.high, size=2)


class DiscreteParameter(Parameter):
    def __init__(self, options: List[T], value: Optional[T] = None) -> None:
        super(DiscreteParameter, self).__init__(value)
        self.options = options

    @property
    def value(self) -> T:
        if self._value is None:
            self.set_random_value()
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        assert value in self.options, f"[DiscreteParameter] Given value '{value}' is not in options '{self.options}'"
        self._value = value

    def set_random_value(self) -> None:
        self._value = np.random.choice(a=self.options)


class MultiDiscreteParameter(Parameter):
    def __init__(self, options: List[T], min_size: int = 0, max_size: Optional[int] = None, value: Optional[T] = None,
                 sorted: bool = False):
        super().__init__(value)
        self.options = options
        self.min_size = min_size
        self.max_size = max_size if max_size is not None else len(options)
        self.sorted = sorted

    @property
    def value(self) -> np.ndarray:
        if self._value is None:
            self.set_random_value()
        if self.sorted:
            self._value = np.array(sorted(self._value))
        return self._value

    @value.setter
    def value(self, value) -> None:
        for v in value:
            assert v in self.options, f"[MultiDiscreteParameter] Given value '{v}' is not in options '{self.options}'"
        self._value = value

    def set_random_value(self) -> None:
        num_parameters = np.random.randint(low=self.min_size, high=self.max_size + 1)
        self._value = np.random.choice(a=self.options, size=num_parameters, replace=False)
