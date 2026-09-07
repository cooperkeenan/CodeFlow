import re

_BRACE_PARAM = re.compile(r"\{([^{}]+)\}")
_ANGLE_PARAM = re.compile(r"<([^<>]+)>")
_METHOD_TOKEN = re.compile(r"^[A-Z]+$")


class RouteLabel:
    def parse(self, label: str) -> tuple[str, str]:
        head, sep, rest = label.partition(" ")
        if sep and _METHOD_TOKEN.match(head):
            return head, rest
        return "", label

    def path_params(self, path: str) -> list[str]:
        names: list[str] = []
        for match in re.finditer(r"\{[^{}]+\}|<[^<>]+>", path):
            token = match.group(0)
            if token.startswith("{"):
                name = _BRACE_PARAM.match(token).group(1)
            else:
                content = _ANGLE_PARAM.match(token).group(1)
                name = content.rsplit(":", 1)[-1]
            if name not in names:
                names.append(name)
        return names
