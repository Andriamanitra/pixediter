from collections.abc import Iterator

# TODO: refactor to use a dedicated tool class that contains all of the drawing logic too
Tool = str


class ToolSelector:
    def __init__(self, *tools: Tool):
        self.tools = tools
        self._current_idx = 0

    def select(self, tool_name: str) -> Tool:
        """
        Select a tool by specifying its name.
        Does nothing if tool with the given name does not exist.
        Returns selected tool.
        """
        for idx, tool in enumerate(self.tools):
            if tool == tool_name:
                self._current_idx = idx
                break
        return self.current

    def select_by_index(self, i: int) -> Tool:
        """
        Select a tool by specifying its index in the tools list.
        Does nothing if specified index was invalid.
        Returns selected tool.
        """
        if 0 <= i < len(self.tools):
            self._current_idx = i
        return self.current

    def __len__(self) -> int:
        return len(self.tools)

    def __iter__(self) -> Iterator[Tool]:
        return (tool for tool in self.tools)

    @property
    def current(self) -> Tool:
        """Return the currently selected tool"""
        return self.tools[self._current_idx]
