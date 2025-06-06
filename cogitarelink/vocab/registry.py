"""Typed, query-able vocabulary registry for CogitareLink."""

from __future__ import annotations

import hashlib, json, importlib.resources as pkg
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Union

# Optional httpx for remote context fetching
try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    _HAS_HTTPX = False
from pydantic import BaseModel, Field, AnyUrl, model_validator
from urllib.parse import urlparse, urlunparse

from ..core.debug import get_logger
from ..core.cache import InMemoryCache

__all__ = ['log', 'registry', 'ContextBlock', 'Versions', 'VocabEntry', 'preferred_collision']

log = get_logger("registry")

# optional rdflib backend
try:
    from rdflib import Graph
    _HAS_RDFLIB = True
except ModuleNotFoundError:
    _HAS_RDFLIB = False

_cache = InMemoryCache(maxsize=256)          # shared cache instance

@_cache.memoize("http")
def _http_get(url: str) -> bytes:
    "10 s-timeout HTTP GET with namespace-scoped cache."
    if not _HAS_HTTPX:
        raise RuntimeError("httpx required for remote context fetching. Install with: pip install httpx")
    log.debug(f"GET {url}")
    r = httpx.get(url, follow_redirects=True, timeout=10)
    r.raise_for_status()
    return r.content

class ContextBlock(BaseModel):
    "Exactly **one** of `url`, `inline`, `derives_from` must be provided."
    url:          AnyUrl | None = None        # remote .jsonld
    inline:       Dict[str, Any] | None = None
    derives_from: AnyUrl | None = None        # .ttl, .rdf, …

    sha256: str | None = None                # filled on first fetch

    @model_validator(mode="after")
    def _single_source(cls, v):
        if sum(x is not None for x in (v.url, v.inline, v.derives_from)) != 1:
            raise ValueError("Provide exactly one of url / inline / derives_from")
        return v

class Versions(BaseModel):
    current:   str
    supported: List[str] = Field(default_factory=list)

class VocabEntry(BaseModel):
    prefix:    str
    uris:      Dict[str, Union[AnyUrl, List[AnyUrl]]]  # {"primary": .., "alternates":[..]}
    context:   ContextBlock
    versions:  Versions

    features:  set[str] = Field(default_factory=set)
    tags:      set[str] = Field(default_factory=set)
    strategy_defaults: Dict[str, str] = Field(default_factory=dict)
    meta:      Dict[str, Any] = Field(default_factory=dict)

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #
    def context_payload(self) -> Dict[str, Any]:
        "Return (and cache) the merged JSON-LD @context dict."
        return _load_ctx(self.prefix, self.versions.current)   # see below

@lru_cache(maxsize=256)
def _load_ctx(prefix: str, version: str) -> Dict[str, Any]:
    """Internal LRU-cached loader for a given prefix+version."""
    e = registry[prefix]

    # pick raw bytes -----------------------------------------------------
    if e.context.inline is not None:                     # already a dict
        raw_dict = e.context.inline
    elif e.context.url is not None:                      # remote .jsonld
        raw_dict = json.loads(_http_get(str(e.context.url)))
    else:                                                # derives_from *.ttl
        if not _HAS_RDFLIB:
            raise RuntimeError("Deriving context requires `rdflib` installed")
        ttl = _http_get(str(e.context.derives_from))
        g = Graph().parse(data=ttl, format="turtle")
        raw_dict = {"@context": {p: str(iri) for p, iri in g.namespaces()}}

    # compute sha once and persist back into in-memory entry -------------
    s = hashlib.sha256(
        json.dumps(raw_dict, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    e.context.sha256 = s

    return raw_dict

class _Registry:
    "Read-only registry; supports prefix *and* alias URL look-ups."

    def __init__(self):
        # For now, use a simplified registry - will enhance with data files later
        self._v: Dict[str, VocabEntry] = {}
        self._alias: Dict[str, str] = {}
        
        # Initialize with basic vocabularies inline
        self._init_basic_vocabs()
        
        # Try to load from data file if available
        try:
            fp = pkg.files("cogitarelink").joinpath("data/registry_data.json")
            raw: Dict[str, Any] = json.loads(fp.read_text())
            for k, v in raw.items():
                self._v[k] = VocabEntry(**v)
        except (FileNotFoundError, ModuleNotFoundError):
            log.debug("Registry data file not found, using basic vocabularies only")

        # build alias map → prefix
        for p, e in self._v.items():
            for url in e.uris.values():
                if isinstance(url, list):
                    for u in url:
                        self._alias[self._norm(str(u))] = p
                else:
                    self._alias[self._norm(str(url))] = p

    def _init_basic_vocabs(self):
        """Initialize basic vocabularies inline for immediate use."""
        # Schema.org vocabulary
        self._v["schema"] = VocabEntry(
            prefix="schema",
            uris={
                "primary": "https://schema.org/",
                "alternates": ["http://schema.org/", "https://schema.org", "http://schema.org"]
            },
            context=ContextBlock(inline={
                "@context": {
                    "name": "http://schema.org/name",
                    "Person": "http://schema.org/Person",
                    "Organization": "http://schema.org/Organization"
                }
            }),
            versions=Versions(current="latest", supported=["latest"]),
            features={"inline_context", "basic_types"},
            tags={"general", "semantic_web"}
        )
        
        # Add alias for schema.org  
        self._v["schema.org"] = self._v["schema"]
        
        # Bioschemas vocabulary (extends Schema.org)
        self._v["bioschemas"] = VocabEntry(
            prefix="bioschemas",
            uris={
                "primary": "https://bioschemas.org/",
                "alternates": ["http://bioschemas.org/"]
            },
            context=ContextBlock(inline={
                "@context": {
                    # Core schema.org terms (note: @type is a reserved keyword, don't redefine)
                    "name": "http://schema.org/name",
                    "identifier": "http://schema.org/identifier",
                    # Bioschemas extensions
                    "Protein": "https://bioschemas.org/Protein",
                    "Gene": "https://bioschemas.org/Gene",
                    "hasSequence": "https://bioschemas.org/hasSequence"
                }
            }),
            versions=Versions(current="latest", supported=["latest"]),
            features={"biological", "structured_data", "schema_extension"},
            tags={"biology", "life_sciences", "schema_org"}
        )

    # ---------------- basic mapping protocol --------------------------
    def __getitem__(self, p: str) -> VocabEntry:
        return self._v[p]

    def __iter__(self):
        return iter(self._v.values())

    # ---------------- convenience helpers ----------------------------
    def resolve(self, ident: str) -> VocabEntry:
        "Accept prefix **or** any alias URI."
        if ident in self._v:
            return self._v[ident]
        try:
            return self._v[self._alias[self._norm(ident)]]
        except KeyError as e:
            raise KeyError(f"{ident!r} not found in registry") from e

    @staticmethod
    def _norm(u: str) -> str:
        p = urlparse(str(u))
        return urlunparse((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"),
                           "", "", ""))


registry = _Registry()

def preferred_collision(a: str, b: str) -> Dict[str, str] | None:
    """Return strategy hint if vocab *a* nominates one for *b*."""
    try:
        return registry[a].strategy_defaults.get(b)     # type: ignore
    except KeyError:
        return None