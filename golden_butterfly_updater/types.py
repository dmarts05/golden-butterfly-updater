class SecretStr:
    """
    Wrapper for sensitive strings to prevent accidental logging or printing.
    """

    def __init__(self, value: str):
        self._value = value

    def __repr__(self) -> str:
        return "**********"

    def __str__(self) -> str:
        return "**********"

    def get_secret_value(self) -> str:
        """
        Returns the actual secret value.
        :return: The secret string value.
        """
        return self._value
