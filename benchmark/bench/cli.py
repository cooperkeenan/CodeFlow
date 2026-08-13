import argparse
import sys
from pathlib import Path

from bench.config.corpus_model import CorpusLoader, CorpusRepo
from bench.config.settings import Settings, get_settings
from bench.corpus.checkout import RepoCheckout
from bench.corpus.pin import CommitPinner, utc_now_iso

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def build_loader() -> CorpusLoader:
    return CorpusLoader(CONFIG_DIR / "corpus.yaml", CONFIG_DIR / "corpus.lock.json")


def select(loader: CorpusLoader, args: argparse.Namespace) -> list[CorpusRepo]:
    if args.all:
        return list(loader.load())
    if not args.repo:
        raise SystemExit(
            "Select a repo with --repo NAME, or pass --all to sweep the whole corpus.\n"
            "Defaulting to a full sweep would be an expensive surprise, so it is not the default."
        )
    return [loader.get(name) for name in args.repo]


def cmd_corpus_list(args: argparse.Namespace, settings: Settings) -> int:
    loader = build_loader()
    pins = loader.pins()
    print(f"{'repo':<30} {'pinned':<14} {'entry truth':<12} condition")
    for repo in loader.load():
        pin = pins.get(repo.name)
        sha = pin.sha[:12] if pin else "-"
        flag = " (control)" if repo.control else ""
        print(f"{repo.name:<30} {sha:<14} {repo.entry_point_truth:<12} {repo.condition}{flag}")
    return 0


def cmd_corpus_pin(args: argparse.Namespace, settings: Settings) -> int:
    loader = build_loader()
    pinner = CommitPinner()
    now = utc_now_iso()
    resolved = {}
    failures = 0
    for repo in select(loader, args):
        try:
            pin = pinner.resolve(repo, now)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            print(f"FAIL  {repo.name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        resolved[repo.name] = pin
        print(f"ok    {repo.name:<28} {pin.sha}")
    if resolved:
        loader.write_pins(resolved)
        print(f"\nwrote {len(resolved)} pin(s) to corpus.lock.json")
    if failures:
        print(f"{failures} repo(s) failed to resolve", file=sys.stderr)
    return 1 if failures else 0


def cmd_corpus_sync(args: argparse.Namespace, settings: Settings) -> int:
    loader = build_loader()
    checkout = RepoCheckout(settings.CORPUS_CACHE_DIR)
    failures = 0
    for repo in select(loader, args):
        try:
            pinned = loader.pinned(repo.name)
            path = checkout.ensure(pinned)
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            print(f"FAIL  {repo.name}: {exc}", file=sys.stderr)
            failures += 1
            continue
        count = sum(1 for _ in path.rglob("*.py"))
        print(f"ok    {pinned.slug:<40} {count:>5} .py files")
    if failures:
        print(f"{failures} repo(s) failed to sync", file=sys.stderr)
    return 1 if failures else 0


def cmd_not_yet(args: argparse.Namespace, settings: Settings) -> int:
    print(f"`{args.command}` is not implemented yet.", file=sys.stderr)
    return 2


def add_selection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", action="append", help="repo name; repeatable")
    parser.add_argument("--all", action="store_true", help="operate on the whole corpus")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench", description="CodeFlow benchmark harness")
    subs = parser.add_subparsers(dest="command", required=True)

    corpus = subs.add_parser("corpus", help="manage the pinned repository corpus")
    corpus_subs = corpus.add_subparsers(dest="subcommand", required=True)

    listing = corpus_subs.add_parser("list", help="show corpus and pin status")
    listing.set_defaults(handler=cmd_corpus_list)

    pinning = corpus_subs.add_parser("pin", help="resolve refs to commit SHAs")
    add_selection(pinning)
    pinning.set_defaults(handler=cmd_corpus_pin)

    sync = corpus_subs.add_parser("sync", help="check out pinned repos locally")
    add_selection(sync)
    sync.set_defaults(handler=cmd_corpus_sync)

    for name, help_text in (
        ("truth", "build or verify Tier 1 ground truth"),
        ("run", "score a repo against ground truth and/or the judge"),
        ("report", "render a previous run"),
    ):
        placeholder = subs.add_parser(name, help=help_text)
        placeholder.set_defaults(handler=cmd_not_yet)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.handler(args, get_settings()))


if __name__ == "__main__":
    raise SystemExit(main())
