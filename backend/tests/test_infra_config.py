"""
Config-presence smoke tests for FINDING-010 and FINDING-011.

Docker/Caddy are not available in this test environment, so these tests do
not start either — they assert that the checked-in configuration files
contain the specific directives the remediation depends on, so a future
edit cannot silently drop them. Real behaviour (TLS handshake, actual
container refusal to start) must still be verified by the reviewer/CI in an
environment with Docker.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    path = REPO_ROOT / relative_path
    if not path.exists():
        pytest.skip(f"{relative_path} not found relative to repo root {REPO_ROOT}")
    return path.read_text()


class TestFinding010CaddyConfig:
    """No TLS / no security headers by default."""

    def test_REQ_SEC_FINDING_010_site_address_driven_by_domain_env(self):
        content = _read("docker/Caddyfile")
        assert "{$DOMAIN}" in content
        assert ":80 {" not in content

    def test_REQ_SEC_FINDING_010_security_headers_present(self):
        content = _read("docker/Caddyfile")
        for header in (
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "Referrer-Policy",
            "Permissions-Policy",
            "Content-Security-Policy",
        ):
            assert header in content, f"missing {header} in docker/Caddyfile"

    def test_REQ_SEC_FINDING_010_widget_route_not_frame_blocked(self):
        """The embeddable interview widget must not carry
        frame-ancestors 'none' — only the admin dashboard/API should."""
        content = _read("docker/Caddyfile")
        assert "handle /interview/*" in content
        widget_block = content.split("handle /interview/*", 1)[1].split("handle {", 1)[0]
        assert "frame-ancestors" not in widget_block

    def test_REQ_SEC_FINDING_010_dev_fallback_is_a_separate_non_default_file(self):
        dev_content = _read("docker/Caddyfile.dev")
        assert ":80 {" in dev_content
        prod_content = _read("docker/Caddyfile")
        assert prod_content != dev_content

    def test_REQ_SEC_FINDING_010_compose_caddy_gets_domain_env(self):
        compose = yaml.safe_load(_read("docker-compose.yml"))
        caddy = compose["services"]["caddy"]
        assert ".env" in caddy.get("env_file", [])


class TestFinding011PostgresPassword:
    """No silent default POSTGRES_PASSWORD."""

    def test_REQ_SEC_FINDING_011_compose_fails_closed(self):
        content = _read("docker-compose.yml")
        assert "POSTGRES_PASSWORD:?" in content
        assert "POSTGRES_PASSWORD:-change-me" not in content

    def test_REQ_SEC_FINDING_011_env_example_has_no_default(self):
        content = _read(".env.example")
        assert "POSTGRES_PASSWORD=change-me" not in content
        assert "POSTGRES_PASSWORD=\n" in content

    def test_REQ_SEC_FINDING_011_config_rejects_placeholder(self):
        """Exercises the actual Settings validator (not just text search)."""
        from app.config import PLACEHOLDER_POSTGRES_PASSWORD, Settings

        with pytest.raises(ValueError):
            Settings(
                postgres_password=PLACEHOLDER_POSTGRES_PASSWORD,
                redis_url="redis://localhost:6379/15",
                secret_key="test-secret-key-for-jwt",
            )

    def test_REQ_SEC_FINDING_011_config_rejects_empty_password(self):
        from app.config import Settings

        with pytest.raises(ValueError):
            Settings(
                postgres_password="",
                redis_url="redis://localhost:6379/15",
                secret_key="test-secret-key-for-jwt",
            )

    def test_REQ_SEC_FINDING_011_config_accepts_real_password(self):
        from app.config import Settings

        s = Settings(
            postgres_password="a-real-generated-password",
            redis_url="redis://localhost:6379/15",
            secret_key="test-secret-key-for-jwt",
        )
        assert s.postgres_password == "a-real-generated-password"


class TestFinding015TrustedProxy:
    """FINDING-015: rate limiting, lockout and audit lines must key on the
    real client address, not Caddy's — which requires (a) the backend to
    only trust X-Forwarded-For from Caddy's own address, and (b) that
    address to be deterministic, which requires a fixed subnet."""

    def test_REQ_SEC_FINDING_015_oasis_net_has_a_fixed_subnet(self):
        compose = yaml.safe_load(_read("docker-compose.yml"))
        oasis_net = compose["networks"]["oasis_net"]
        subnets = [c["subnet"] for c in oasis_net["ipam"]["config"]]
        assert "172.28.0.0/24" in subnets

    def test_REQ_SEC_FINDING_015_default_trusted_proxy_ips_matches_subnet(self):
        from app.config import Settings

        s = Settings(
            postgres_password="test",
            redis_url="redis://localhost:6379/15",
            secret_key="test-secret-key-for-jwt",
        )
        assert s.trusted_proxy_ips == "172.28.0.0/24"

    def test_REQ_SEC_FINDING_015_caddyfile_overwrites_inbound_xff(self):
        content = _read("docker/Caddyfile")
        assert "header_up X-Forwarded-For {http.request.remote.host}" in content
        # Both the API and the WebSocket blocks proxy to the backend and
        # must carry the same treatment.
        assert content.count("header_up X-Forwarded-For {http.request.remote.host}") >= 2

    def test_REQ_SEC_FINDING_015_main_registers_proxy_headers_middleware(self):
        content = _read("backend/app/main.py")
        assert "ProxyHeadersMiddleware" in content
        assert "trusted_hosts=settings.trusted_proxy_ips" in content
