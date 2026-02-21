"""Base runtime miner interfaces."""


class RuntimeMiner:
    """Base interface for runtime data miners."""

    def parse(self, path: str) -> list[dict[str, str]]:
        """Parse runtime data file.

        Args:
            path: Runtime trace or log path.

        Returns:
            list[dict[str, str]]: Parsed runtime relationships.
        """
        return []
