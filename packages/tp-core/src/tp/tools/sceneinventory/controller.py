from __future__ import annotations

from tp.core.host import current_host, Host


class SceneInventoryController:
    def __init__(self, host: Host | None = None):
        super().__init__()

        self._host = host or current_host()
        self._current_project_name: str | None = None

    def get_current_context(self) -> dict[str, str]:
        pass

    def get_current_project_name(self) -> str:
        if self._current_project_name is None:
            try:
                self._current_project_name = self.get_current_context()["project_name"]
            except KeyError:
                raise RuntimeError(
                    "Current project name could not be "
                    "determined from the host context."
                )

        return self._current_project_name
