"""How a `RequirementSpec` is named in NX, and the bookkeeping line that records its identity.

The NX name is for people (it shows in the Part Navigator and the Expressions dialog), so it is readable but lossy:
non-alphanumerics become '_'. The exact identity therefore travels in a bookkeeping line appended to the
requirement's description, and that line, not the name, decides ownership on read. A name can collide only for two
keys differing purely in punctuation; `RequirementDiff` refuses such a set rather than letting one overwrite the
other.

Internal to Foundation: not part of the public API.
"""

from collections.abc import Sequence
from urllib.parse import quote, unquote

from banxopen.foundation.model.requirements import RequirementSpec

Identity = tuple[str, str, str]
"""(domain, key, aspect)."""

_PREFIX = "BA_REQ_"
"""Every requirement the BANxOpen tools write starts with this."""

_METADATA_MARKER = "#BA_REQ v1"

_URI_UNRESERVED = "-._~"
"""RFC 3986 unreserved punctuation: the characters C#'s Uri.EscapeDataString leaves alone besides letters/digits."""


def name_from_identity(domain: str, key: str, aspect: str) -> str:
    """`BA_REQ_<DOMAIN>_<KEY>_<ASPECT>`, upper-cased, each part reduced to letters, digits and '_'. A separator is
    kept for every punctuation character, so `B1005010-2` and `B10050102` stay distinct."""
    return f"{_PREFIX}{_token(domain)}_{_token(key)}_{_token(aspect)}"


def requirement_name(spec: RequirementSpec) -> str:
    """From `spec.name_stem` when it has one (`BA_REQ_<STEM>_<ASPECT>`), else from its identity."""
    if not spec.name_stem:
        return name_from_identity(spec.domain, spec.key, spec.aspect)
    return f"{_PREFIX}{_token(spec.name_stem)}_{_token(spec.aspect)}"


def check_name(requirement_name: str) -> str:
    """The name of the Requirement Check that links a requirement to its checked expression."""
    return f"{requirement_name}_CHK"


def description_with_metadata(spec: RequirementSpec) -> tuple[str, ...]:
    """The description as written to NX: the domain's own lines, then the bookkeeping line."""
    return (*spec.description, _metadata_line(spec.domain, spec.key, spec.aspect))


def split_description(lines: Sequence[str]) -> tuple[tuple[str, ...], Identity | None]:
    """Splits a description read from NX into the domain's own lines and the identity the bookkeeping line carries.

    The identity is None when there is no well-formed line: a requirement someone else wrote, or one edited by hand.
    Raises ValueError when a bookkeeping line repeats a field.
    """
    own: list[str] = []
    identity: Identity | None = None
    for line in lines:
        parsed = _parse_metadata(line) if identity is None else None
        if parsed is not None:
            identity = parsed
        else:
            own.append(line)
    return tuple(own), identity


def _metadata_line(domain: str, key: str, aspect: str) -> str:
    return f"{_METADATA_MARKER} domain={_escape(domain)} key={_escape(key)} aspect={_escape(aspect)}"


def _parse_metadata(line: str) -> Identity | None:
    if not line.startswith(_METADATA_MARKER + " "):
        return None

    fields: dict[str, str] = {}
    for part in line[len(_METADATA_MARKER) + 1 :].split(" "):
        name, sep, value = part.partition("=")
        if not sep:
            continue
        if name in fields:
            raise ValueError(f"bookkeeping line repeats the field '{name}'")
        fields[name] = value

    try:
        return unquote(fields["domain"]), unquote(fields["key"]), unquote(fields["aspect"])
    except KeyError:
        return None


def _escape(value: str) -> str:
    return quote(value, safe=_URI_UNRESERVED)


def _token(value: str) -> str:
    # One output character per UTF-16 unit, as the C# original: a character outside the BMP is two units.
    return "".join("__" if ord(c) > 0xFFFF else c.upper() if c.isascii() and c.isalnum() else "_" for c in value)
