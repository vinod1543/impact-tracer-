"""Base infrastructure parser interfaces."""


class InfraParser:
    """Base interface for infrastructure parser implementations."""

    def parse(self, path: str) -> list[dict[str, str]]:
        """Parse an infrastructure file.

        Args:
            path: Path to infra config file.

        Returns:
            list[dict[str, str]]: Parsed entities.
        """
        return []
