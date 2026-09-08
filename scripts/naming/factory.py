import os
from pathlib import Path

from naming.banks import Bank
from naming.contracts import CandidateSource, Probe
from naming.dns_probe import DnsProbe
from naming.dns_resolver import DnsResolver
from naming.github_probe import GithubRepoProbe
from naming.http_client import HttpClient
from naming.morpheme_generator import MorphemeGenerator
from naming.pipeline import NameSearchPipeline
from naming.prober import CandidateProber
from naming.rdap_probe import RdapProbe
from naming.registry_probe import NPM_URL, PYPI_URL, PackageRegistryProbe
from naming.reporter import ConsoleReporter
from naming.seed_source import SeedSource
from naming.store import NameStore
from naming.variant_source import VariantSource
from naming.verdict import VerdictAggregator


def build_probes(http: HttpClient, rdap_base: str, github_token: str) -> tuple[Probe, ...]:
    return (
        RdapProbe(http, rdap_base),
        DnsProbe(DnsResolver()),
        PackageRegistryProbe("pypi", PYPI_URL, http),
        PackageRegistryProbe("npm", NPM_URL, http),
        GithubRepoProbe(http, github_token),
    )


def build_pipeline(
    db_path: Path,
    store: NameStore,
    rdap_base: str,
    bank: Bank,
    batch_size: int = 8,
    workers: int = 4,
    pause_s: float = 0.0,
    verbose: bool = False,
    use_variants: bool = True,
) -> NameSearchPipeline:
    http = HttpClient()
    probes = build_probes(http, rdap_base, os.environ.get("GITHUB_TOKEN", ""))
    prober = CandidateProber(probes, VerdictAggregator(), workers)
    sources: tuple[CandidateSource, ...] = (SeedSource(bank.seeds),)
    if use_variants:
        sources += (VariantSource(store),)
    sources += (MorphemeGenerator(bank.roots, bank.suffixes),)
    return NameSearchPipeline(
        sources=sources,
        prober=prober,
        store=store,
        reporter=ConsoleReporter(verbose),
        db_label=str(db_path),
        batch_size=batch_size,
        pause_s=pause_s,
    )
