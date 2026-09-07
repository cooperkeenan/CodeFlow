import re

_SPLIT_PATTERN = re.compile(r"[_\s]+")


class HandlerName:
    def humanize(self, handler_fqn: str) -> str:
        name = handler_fqn.rsplit(".", 1)[-1]
        words = [word for word in _SPLIT_PATTERN.split(name) if word]
        if not words:
            return name
        sentence = " ".join(words).lower()
        return sentence[0].upper() + sentence[1:]
