"""
Tests for FINDING-007's SSRF guard on operator-configurable provider
endpoint URLs (app/egress_guard.py).
"""

import pytest

from app.config import settings
from app.egress_guard import EgressURLError, validate_egress_url


@pytest.fixture(autouse=True)
def _reset_allowed_private_hosts():
    """`EGRESS_ALLOWED_PRIVATE_HOSTS` defaults to empty; tests that need a
    private http destination allow-listed set it explicitly and this
    fixture restores the original value afterwards, isolating tests."""
    original = settings.egress_allowed_private_hosts
    yield
    settings.egress_allowed_private_hosts = original


class TestValidateEgressUrl:
    def test_empty_url_is_allowed(self):
        """Clearing a field (empty string) is always allowed."""
        validate_egress_url("", field="self_hosted_stt_url")  # must not raise

    def test_https_public_host_allowed(self):
        """test_REQ_SEC_FINDING_007_https_public_allowed

        Uses a real, always-resolvable public domain (RFC 2606 reserved)
        rather than a fabricated subdomain — this guard now fails closed on
        an unresolvable host (see test_unresolvable_host_rejected below), so
        a placeholder that does not actually resolve is no longer a valid
        stand-in for "any public https host".
        """
        validate_egress_url("https://example.com/v1", field="embedding_api_url")

    def test_https_private_ip_allowed(self):
        validate_egress_url("https://192.168.1.10:4000/v1", field="self_hosted_stt_url")

    def test_http_private_ip_rejected_by_default(self):
        """FINDING-007 (Revision 4 residual): merely being RFC1918 is no
        longer sufficient for plain http — every private destination used
        to be reachable over http, including sibling containers not in
        `_DENIED_HOSTNAMES`. Now it must be explicitly allow-listed.

        test_REQ_SEC_FINDING_007_http_private_ip_rejected_by_default
        """
        settings.egress_allowed_private_hosts = ""
        with pytest.raises(EgressURLError, match="EGRESS_ALLOWED_PRIVATE_HOSTS"):
            validate_egress_url("http://192.168.1.10:4000/v1", field="self_hosted_stt_url")

    def test_http_private_ip_allowed_when_explicitly_listed(self):
        """test_REQ_SEC_FINDING_007_http_private_ip_allowlisted"""
        settings.egress_allowed_private_hosts = "192.168.1.10"
        validate_egress_url("http://192.168.1.10:4000/v1", field="self_hosted_stt_url")

    def test_http_private_ip_allowed_via_cidr(self):
        """test_REQ_SEC_FINDING_007_http_private_cidr_allowlisted"""
        settings.egress_allowed_private_hosts = "192.168.1.0/24"
        validate_egress_url("http://192.168.1.10:4000/v1", field="self_hosted_stt_url")

    def test_http_private_hostname_allowed_when_listed_by_name(self, monkeypatch):
        """A hostname (not a literal IP) that resolves to a private address
        can also be allow-listed by name, not only by IP/CIDR. DNS is mocked
        so this does not depend on a real `my-litellm` host existing."""
        import socket as socket_module

        def _fake_getaddrinfo(host, *_args, **_kwargs):
            assert host == "my-litellm"
            return [(socket_module.AF_INET, socket_module.SOCK_STREAM, 6, "", ("10.0.5.20", 0))]

        monkeypatch.setattr(socket_module, "getaddrinfo", _fake_getaddrinfo)
        settings.egress_allowed_private_hosts = "my-litellm"
        validate_egress_url("http://my-litellm:4000/v1", field="openai_compatible_llm_url")

    def test_allowlisted_private_host_still_denies_known_internal_service_names(self):
        """`_DENIED_HOSTNAMES` cannot be overridden by the operator allow-list
        — those names have no legitimate use as a provider endpoint."""
        settings.egress_allowed_private_hosts = "postgres,redis"
        with pytest.raises(EgressURLError):
            validate_egress_url("http://postgres:5432", field="self_hosted_stt_url")

    def test_unresolvable_host_rejected(self):
        """FINDING-007 (Revision 4 residual): a DNS failure used to be
        swallowed and treated as "not private", which still blocked http but
        let an unvalidated https URL through with no address check at all.

        test_REQ_SEC_FINDING_007_unresolvable_host_rejected
        """
        with pytest.raises(EgressURLError, match="could not be resolved"):
            validate_egress_url(
                "https://this-host-does-not-exist.invalid/v1", field="embedding_api_url"
            )

    def test_http_public_host_rejected(self):
        """test_REQ_SEC_FINDING_007_http_public_rejected"""
        with pytest.raises(EgressURLError, match="https"):
            validate_egress_url("http://example.com/v1", field="self_hosted_stt_url")

    def test_loopback_rejected(self):
        """test_REQ_SEC_FINDING_007_loopback_rejected"""
        with pytest.raises(EgressURLError):
            validate_egress_url("http://127.0.0.1:9000/v1", field="self_hosted_stt_url")

    def test_link_local_metadata_endpoint_rejected(self):
        """FINDING-007: blocks the exact cloud-metadata SSRF example cited
        in the finding (169.254.169.254).

        test_REQ_SEC_FINDING_007_metadata_endpoint_rejected
        """
        with pytest.raises(EgressURLError):
            validate_egress_url("http://169.254.169.254/latest/meta-data/", field="embedding_api_url")

    def test_sibling_container_hostname_rejected(self):
        """FINDING-007: blocks the exact internal-service SSRF examples
        cited in the finding (postgres, redis).

        test_REQ_SEC_FINDING_007_sibling_container_rejected
        """
        with pytest.raises(EgressURLError):
            validate_egress_url("http://postgres:5432", field="self_hosted_stt_url")
        with pytest.raises(EgressURLError):
            validate_egress_url("http://redis:6379", field="self_hosted_stt_url")

    def test_embedded_credentials_rejected(self):
        """test_REQ_SEC_FINDING_007_embedded_credentials_rejected"""
        with pytest.raises(EgressURLError, match="credentials"):
            validate_egress_url(
                "https://user:pass@api.example.com/v1", field="embedding_api_url"
            )

    def test_invalid_scheme_rejected(self):
        with pytest.raises(EgressURLError):
            validate_egress_url("ftp://api.example.com/v1", field="embedding_api_url")

    def test_missing_host_rejected(self):
        with pytest.raises(EgressURLError):
            validate_egress_url("https:///path-only", field="embedding_api_url")
