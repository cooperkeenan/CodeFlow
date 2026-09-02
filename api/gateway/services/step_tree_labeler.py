_KEY_SEP = "::"


class StepTreeLabeler:
    def flatten(self, steps_by_fqn: dict[str, list]) -> list[dict]:
        flat: list[dict] = []
        for fqn in sorted(steps_by_fqn):
            self._flatten_steps(steps_by_fqn[fqn], fqn, flat)
        return flat

    def _flatten_steps(self, steps: list[dict], owner_fqn: str, out: list[dict]) -> None:
        for step in steps:
            if step.get("kind") != "more":
                out.append(
                    {
                        "id": self._key(owner_fqn, step["id"]),
                        "kind": step["kind"],
                        "raw": step.get("raw", ""),
                        "label": step.get("label", ""),
                        "owner_fqn": owner_fqn,
                    }
                )
            for arm in step.get("arms", []):
                self._flatten_steps(arm.get("steps", []), owner_fqn, out)
            if "body" in step:
                self._flatten_steps(step["body"], owner_fqn, out)

    def apply(self, steps_by_fqn: dict[str, list], labels: dict[str, str]) -> dict[str, list]:
        return {
            fqn: [self._apply_step(s, labels, fqn) for s in steps]
            for fqn, steps in steps_by_fqn.items()
        }

    def _apply_step(self, step: dict, labels: dict[str, str], owner_fqn: str) -> dict:
        new_step = dict(step)
        key = self._key(owner_fqn, step["id"])
        if step.get("kind") != "more" and key in labels:
            new_step["llm_label"] = labels[key]
        if "arms" in step:
            new_step["arms"] = [
                {**arm, "steps": [self._apply_step(s, labels, owner_fqn) for s in arm.get("steps", [])]}
                for arm in step["arms"]
            ]
        if "body" in step:
            new_step["body"] = [self._apply_step(s, labels, owner_fqn) for s in step["body"]]
        return new_step

    def _key(self, owner_fqn: str, step_id: str) -> str:
        return f"{owner_fqn}{_KEY_SEP}{step_id}"
