import json
from pathlib import Path

from evaluation.answer_sheet.schema import AnswerSheet

_OUTPUTS = Path(__file__).parent.parent / "shared" / "outputs"
_FIXTURE = Path(__file__).parent / "answer_sheet" / "codeflow.json"


def load_spec(outputs_dir: Path = _OUTPUTS) -> dict:
    for name in ("tracer.json", "tracer_output.json"):
        p = outputs_dir / name
        if p.exists():
            data = json.loads(p.read_text())
            if "diagram_spec" in data:
                return data["diagram_spec"]
            if "trace" in data and "diagram_spec" in data["trace"]:
                return data["trace"]["diagram_spec"]
    raise FileNotFoundError(f"No tracer output found in {outputs_dir}")


def load_fixture(fixture_path: Path = _FIXTURE) -> AnswerSheet:
    return AnswerSheet.from_dict(json.loads(fixture_path.read_text()))
