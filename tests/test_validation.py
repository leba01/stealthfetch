"""Tests for URL and proxy validation."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from stealthfetch._errors import validate_proxy, validate_url


class TestURLValidation:
    def test_valid_https(self) -> None:
        validate_url("https://example.com")  # should not raise

    def test_valid_http(self) -> None:
        validate_url("http://example.com")  # should not raise

    @pytest.mark.parametrize(
        "url",
        [
            "file:///etc/passwd",
            "javascript:alert(1)",
            "ftp://example.com/file",
        ],
        ids=["file", "javascript", "ftp"],
    )
    def test_bad_scheme_rejected(self, url: str) -> None:
        with pytest.raises(ValueError, match="not allowed"):
            validate_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://10.0.0.1/",
            "http://192.168.1.1/",
            "http://169.254.169.254/latest/meta-data/",
        ],
        ids=["loopback", "10.x", "192.168", "link-local"],
    )
    def test_private_ip_rejected(self, url: str) -> None:
        with pytest.raises(ValueError, match="private"):
            validate_url(url)

    def test_empty_url_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_url("")

    def test_whitespace_url_rejected(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            validate_url("   ")

    def test_hostname_allowed(self) -> None:
        validate_url("https://www.google.com")  # should not raise

    def test_no_hostname_rejected(self) -> None:
        with pytest.raises(ValueError, match="no hostname"):
            validate_url("http://")

    def test_zero_ip_rejected(self) -> None:
        with pytest.raises(ValueError, match="private"):
            validate_url("http://0.0.0.0/")


class TestSSRFDNSResolution:
    """Tests for DNS-resolution-based SSRF protection."""

    def _mock_getaddrinfo(self, ip: str):  # type: ignore[no-untyped-def]
        """Return a mock getaddrinfo result resolving to the given IP."""
        return [(2, 1, 6, "", (ip, 0))]

    def test_localhost_rejected(self) -> None:
        with (
            patch(
                "stealthfetch._errors.socket.getaddrinfo",
                return_value=self._mock_getaddrinfo("127.0.0.1"),
            ),
            pytest.raises(ValueError, match="private/loopback"),
        ):
            validate_url("http://localhost/")

    def test_ipv6_loopback_literal_rejected(self) -> None:
        with pytest.raises(ValueError, match="private"):
            validate_url("http://[::1]/")

    def test_ipv6_mapped_ipv4_rejected(self) -> None:
        """IPv6-mapped IPv4 like ::ffff:127.0.0.1 should be caught."""
        with (
            patch(
                "stealthfetch._errors.socket.getaddrinfo",
                return_value=[(10, 1, 6, "", ("::ffff:127.0.0.1", 0, 0, 0))],
            ),
            pytest.raises(ValueError, match="private/loopback"),
        ):
            validate_url("http://evil.example.com/")

    def test_hostname_resolving_to_private_rejected(self) -> None:
        with (
            patch(
                "stealthfetch._errors.socket.getaddrinfo",
                return_value=self._mock_getaddrinfo("10.0.0.1"),
            ),
            pytest.raises(ValueError, match="private/loopback"),
        ):
            validate_url("http://attacker.com/")

    def test_hostname_resolving_to_metadata_rejected(self) -> None:
        with (
            patch(
                "stealthfetch._errors.socket.getaddrinfo",
                return_value=self._mock_getaddrinfo("169.254.169.254"),
            ),
            pytest.raises(ValueError, match="private/loopback"),
        ):
            validate_url("http://attacker.com/")

    def test_unresolvable_hostname_allowed(self) -> None:
        """DNS failure should not block — let the fetch layer handle it."""
        import socket

        with patch(
            "stealthfetch._errors.socket.getaddrinfo",
            side_effect=socket.gaierror("Name resolution failed"),
        ):
            validate_url("http://nonexistent.example.com/")  # should not raise


class TestProxyValidation:
    def test_valid_proxy(self) -> None:
        validate_proxy({"server": "http://proxy:8080"})  # should not raise

    def test_proxy_with_creds(self) -> None:
        validate_proxy(
            {"server": "http://proxy:8080", "username": "u", "password": "p"}
        )  # should not raise

    def test_missing_server_rejected(self) -> None:
        with pytest.raises(ValueError, match="server"):
            validate_proxy({"username": "u"})

    def test_empty_proxy_rejected(self) -> None:
        with pytest.raises(ValueError, match="server"):
            validate_proxy({})
