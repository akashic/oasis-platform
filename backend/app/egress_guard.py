"""
OASIS — SSRF guard for operator-configurable provider endpoint URLs.

FINDING-007: ``openai_compatible_llm_url``, ``azure_openai_endpoint``,
``self_hosted_stt_url``, ``self_hosted_tts_url``, ``embedding_api_url`` and
``audio_s3_endpoint_url`` are written via ``PUT /api/settings/keys`` /
``PUT /api/settings/audio-storage`` and are then used directly as outbound
request destinations (``smoke.py``, ``text_chat.py``, ``pipeline/runner.py``,
``audio/storage.py``). That allows silent redirection of participant
audio/transcripts to an attacker-controlled host, and SSRF against cloud
metadata (``169.254.169.254``) or sibling containers (``postgres``,
``redis``).

``validate_egress_url`` is called both when a URL is written
(``app/api/settings.py``) and immediately before each outbound request
(``app/providers/smoke.py``, ``app/api/text_chat.py``,
``app/pipeline/runner.py``, ``app/audio/storage.py``) so a DNS record that
resolves safely at write time and unsafely at request time (DNS rebinding)
is still caught.

FINDING-007 (Revision 4 residual): plain ``http`` used to be allowed to
*any* private (RFC1918/loopback-adjacent) address — which meant every
sibling container was reachable over http by IP, and by any Compose alias
not in ``_DENIED_HOSTNAMES`` (a fixed 5-name list). Plain http destinations
now require the host to be explicitly present in
``settings.egress_allowed_private_hosts`` (``EGRESS_ALLOWED_PRIVATE_HOSTS``)
— an operator opt-in allow-list of hostnames/IPs/CIDRs — closing that gap
without banning self-hosted providers on a private network outright.
An unresolvable hostname is now also a hard failure rather than silently
treated as "not private" (which happened to still block http, but let an
unresolvable https host through with no validation at all).
"""

import ipaddress
import socket
from urllib.parse import urlsplit

# Docker Compose service hostnames on ``oasis_net`` that must never be
# reachable via an operator-configured provider endpoint — closes the exact
# SSRF examples in FINDING-007 (``http://postgres:5432``, ``http://redis:6379``).
# Denied regardless of scheme and regardless of `EGRESS_ALLOWED_PRIVATE_HOSTS`
# — these names have no legitimate use as a provider endpoint.
_DENIED_HOSTNAMES = {"postgres", "redis", "backend", "frontend", "caddy"}


class EgressURLError(ValueError):
    """Raised when a configured provider/egress URL fails SSRF validation."""


def _is_denied_ip(ip: "ipaddress._BaseAddress") -> bool:
    return (
        ip.is_loopback
        or ip.is_link_local  # covers 169.254.0.0/16, incl. cloud metadata
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _parse_allowed_private_hosts(raw: str) -> tuple[set[str], list["ipaddress._BaseNetwork"]]:
    """Split ``EGRESS_ALLOWED_PRIVATE_HOSTS`` into literal hostnames/IPs and
    CIDR networks. Invalid entries are ignored rather than raising — this
    runs on every validation call, and a startup-config typo here must not
    turn into a crash on every settings write or outbound request."""
    literals: set[str] = set()
    networks: list["ipaddress._BaseNetwork"] = []
    for entry in raw.split(","):
        entry = entry.strip().lower()
        if not entry:
            continue
        if "/" in entry:
            try:
                networks.append(ipaddress.ip_network(entry, strict=False))
                continue
            except ValueError:
                pass
        try:
            # A bare IP is also matched as a literal, via exact string
            # comparison against the resolved address below.
            ipaddress.ip_address(entry)
        except ValueError:
            pass
        literals.add(entry)
    return literals, networks


def _is_explicitly_allowed_private_host(
    host: str, resolved_ips: list["ipaddress._BaseAddress"], *, allow_list_raw: str
) -> bool:
    literals, networks = _parse_allowed_private_hosts(allow_list_raw)
    if host.lower() in literals:
        return True
    for ip in resolved_ips:
        if str(ip) in literals:
            return True
        if any(ip in net for net in networks):
            return True
    return False


def validate_egress_url(url: str, *, field: str = "url") -> None:
    """Validate an operator-supplied outbound endpoint URL.

    Raises :class:`EgressURLError` (a ``ValueError``) with a human-readable
    reason on failure. A blank ``url`` is treated as "not configured" and
    always passes (clearing a field is always allowed).
    """
    if not url:
        return

    # Imported lazily to avoid a hard import-time dependency for callers
    # (e.g. tests) that construct a URL guard before settings are loaded.
    from app.config import settings

    parts = urlsplit(url)

    if parts.scheme not in ("http", "https"):
        raise EgressURLError(f"{field}: scheme must be http or https")

    if "@" in (parts.netloc or ""):
        raise EgressURLError(f"{field}: embedded credentials in the URL are not allowed")

    host = parts.hostname
    if not host:
        raise EgressURLError(f"{field}: missing host")

    if host.lower() in _DENIED_HOSTNAMES:
        raise EgressURLError(
            f"{field}: host {host!r} is an internal platform service and is not "
            "a permitted egress destination"
        )

    is_private = False
    resolved_ips: list["ipaddress._BaseAddress"] = []
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None

    if ip is not None:
        if _is_denied_ip(ip):
            raise EgressURLError(
                f"{field}: host {host!r} resolves to a disallowed address"
            )
        is_private = ip.is_private
        resolved_ips = [ip]
    else:
        # Hostname, not a literal IP — resolve it. Re-running this check
        # immediately before each outbound request (not only at write time)
        # is what defeats DNS rebinding between the two checks.
        try:
            resolved = socket.getaddrinfo(host, None)
        except socket.gaierror as exc:
            # FINDING-007: previously swallowed — an unresolvable host fell
            # through with `is_private=False`, which happened to still
            # reject plain http but let an unvalidated https URL through
            # with no address check at all. Fail closed instead.
            raise EgressURLError(
                f"{field}: host {host!r} could not be resolved: {exc}"
            ) from None
        for _family, _type, _proto, _canon, sockaddr in resolved:
            addr = sockaddr[0]
            try:
                resolved_ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            if _is_denied_ip(resolved_ip):
                raise EgressURLError(
                    f"{field}: host {host!r} resolves to a disallowed address ({addr})"
                )
            resolved_ips.append(resolved_ip)
            if resolved_ip.is_private:
                is_private = True

    if parts.scheme == "http" and is_private:
        # FINDING-007: plain http to a private address now requires an
        # explicit operator opt-in — being merely RFC1918 is no longer
        # sufficient, closing the "every sibling container is reachable"
        # gap (the 5-name `_DENIED_HOSTNAMES` list above is a permanent
        # denial; this allow-list is the inverse — a permanent-until-listed
        # default-deny for everything else on the private network).
        if not _is_explicitly_allowed_private_host(
            host, resolved_ips, allow_list_raw=settings.egress_allowed_private_hosts
        ):
            raise EgressURLError(
                f"{field}: plain http to the private host {host!r} requires "
                "it to be listed in EGRESS_ALLOWED_PRIVATE_HOSTS, or use https"
            )
    elif parts.scheme == "http" and not is_private:
        raise EgressURLError(
            f"{field}: plain http is only allowed for private-network (RFC1918) "
            "hosts explicitly listed in EGRESS_ALLOWED_PRIVATE_HOSTS; use https "
            "for public endpoints"
        )
