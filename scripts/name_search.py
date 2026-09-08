import argparse
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from naming.banks import BANKS, DEFAULT_BANK
from naming.factory import build_pipeline
from naming.rdap_probe import BOOTSTRAP_RDAP, VERISIGN_COM_RDAP
from naming.statuses import VERDICT_CHECK, VERDICT_STRONG
from naming.store import NameStore

DEFAULT_DB = SCRIPTS_DIR.parent / "scratch_out" / "naming" / "names.sqlite3"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="name_search.py",
        description="generate startup names, check .com availability and prior art, store the results",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="generate, check and store, round after round")
    run.add_argument("--rounds", type=int, default=4)
    run.add_argument("--batch", type=int, default=8)
    run.add_argument("--workers", type=int, default=4)
    run.add_argument("--pause", type=float, default=1.0)
    run.add_argument("--verbose", action="store_true")
    run.add_argument("--bootstrap-rdap", action="store_true", help="use rdap.org instead of Verisign")
    run.add_argument("--bank", choices=sorted(BANKS), default=DEFAULT_BANK)
    run.add_argument("--no-variants", action="store_true", help="skip get/use/HQ shapes of rejected names")

    check = subparsers.add_parser("check", help="check names given on the command line")
    check.add_argument("names", nargs="+")
    check.add_argument("--workers", type=int, default=4)
    check.add_argument("--verbose", action="store_true")
    check.add_argument("--bootstrap-rdap", action="store_true")
    check.add_argument("--bank", choices=sorted(BANKS), default=DEFAULT_BANK)

    top = subparsers.add_parser("top", help="print the best stored candidates")
    top.add_argument("--limit", type=int, default=25)
    top.add_argument("--all", action="store_true", help="include rejected and unknown names")
    return parser


def _print_top(store: NameStore, limit: int, include_all: bool) -> None:
    verdicts = () if include_all else (VERDICT_STRONG, VERDICT_CHECK)
    rows = store.latest(verdicts, limit)
    if not rows:
        print("nothing stored yet; run `name_search.py run` first")
        return
    for row in rows:
        print(
            f"{row['verdict']:<8} {row['domain']:<22} {row['domain_status']:<17}"
            f" prior art x{row['prior_art_hits']}  {row['rationale']}"
        )


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    store = NameStore(args.db)
    try:
        if args.command == "top":
            _print_top(store, args.limit, args.all)
            return 0
        rdap_base = BOOTSTRAP_RDAP if getattr(args, "bootstrap_rdap", False) else VERISIGN_COM_RDAP
        pipeline = build_pipeline(
            db_path=args.db,
            store=store,
            rdap_base=rdap_base,
            bank=BANKS[args.bank],
            batch_size=getattr(args, "batch", 8),
            workers=args.workers,
            pause_s=getattr(args, "pause", 0.0),
            verbose=args.verbose,
            use_variants=not getattr(args, "no_variants", False),
        )
        if args.command == "check":
            pipeline.check_names(args.names)
            return 0
        pipeline.run(args.rounds)
        return 0
    finally:
        store.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["run"]))
