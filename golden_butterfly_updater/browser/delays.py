import random
from dataclasses import dataclass
from enum import Enum


@dataclass(slots=True, frozen=True)
class DelayValues:
    """
    Delay values for a specific profile.
    """

    navigate_delay: tuple[float, float]
    wait_timeout: float
    action_delay_range: tuple[float, float]


class DelayProfile(Enum):
    """
    Available delay profiles.
    """

    FAST = DelayValues(
        navigate_delay=(2, 3),
        wait_timeout=4,
        action_delay_range=(0.5, 1.5),
    )
    MEDIUM = DelayValues(
        navigate_delay=(4, 5),
        wait_timeout=8,
        action_delay_range=(2, 3),
    )
    SLOW = DelayValues(
        navigate_delay=(6, 7),
        wait_timeout=12,
        action_delay_range=(3, 5),
    )


class Delays:
    """
    Delays for bot actions.
    """

    def __init__(self, profile: DelayProfile) -> None:
        self.__profile = profile

    @property
    def navigate_delay(self) -> float:
        """Navigate delay for the current profile."""
        return random.uniform(*self.__profile.value.navigate_delay)

    @property
    def wait_timeout(self) -> float:
        """Wait timeout for the current profile."""
        return self.__profile.value.wait_timeout

    @property
    def action_delay(self) -> float:
        """A random action delay within the range for the current profile."""
        delay_range = self.__profile.value.action_delay_range
        return random.uniform(*delay_range)
