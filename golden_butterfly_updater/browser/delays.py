import random
from dataclasses import dataclass
from enum import Enum


@dataclass(slots=True, frozen=True, kw_only=True)
class DelayValues:
    """
    Delay values for a specific profile.
    """

    navigate_delay: tuple[float, float]
    """Delay range for navigation actions."""
    wait_timeout: float
    """Wait timeout before considering an action failed."""
    action_delay_range: tuple[float, float]
    """Range for random action delays."""


class DelayProfile(str, Enum):
    """
    Available delay profiles.
    Inherits from str to handle YAML string matching automatically.
    """

    FAST = "FAST"
    MEDIUM = "MEDIUM"
    SLOW = "SLOW"

    @property
    def values(self) -> DelayValues:
        mapping = {
            "FAST": DelayValues(
                navigate_delay=(2, 3), wait_timeout=4, action_delay_range=(0.5, 1.5)
            ),
            "MEDIUM": DelayValues(
                navigate_delay=(4, 5), wait_timeout=8, action_delay_range=(2, 3)
            ),
            "SLOW": DelayValues(
                navigate_delay=(6, 7), wait_timeout=12, action_delay_range=(3, 5)
            ),
        }
        return mapping[self.value]


class Delays:
    """
    Delays for bot actions.
    """

    def __init__(self, profile: DelayProfile) -> None:
        self.__profile = profile

    @property
    def navigate_delay(self) -> float:
        """
        Delay for navigation actions for the current profile.

        :return: A random navigation delay within the range for the current profile.
        """
        return random.uniform(*self.__profile.values.navigate_delay)

    @property
    def wait_timeout(self) -> float:
        """
        Wait timeout for the current profile.

        :return: Wait timeout.
        """
        return self.__profile.values.wait_timeout

    @property
    def action_delay(self) -> float:
        """
        Delay for general actions for the current profile.

        :return: A random action delay within the range for the current profile.
        """
        delay_range = self.__profile.values.action_delay_range
        return random.uniform(*delay_range)
