"""Tests for bounded local IP recovery scans."""

from network_recovery import recovery_hosts


def _adapter(address: str, prefix: int, *, enabled: bool = True) -> dict[str, object]:
    return {
        "enabled": enabled,
        "ipv4": [{"address": address, "network_prefix": prefix}],
    }


def test_recovery_scans_matching_local_subnet() -> None:
    """A changed address can be found in the same local /24."""
    hosts = recovery_hosts("192.168.1.161", [_adapter("192.168.1.108", 24)])

    assert "192.168.1.162" in hosts
    assert "192.168.1.161" not in hosts
    assert len(hosts) == 253


def test_recovery_respects_smaller_local_subnet() -> None:
    """A subnet smaller than /24 is not widened."""
    hosts = recovery_hosts("192.168.1.161", [_adapter("192.168.1.130", 25)])

    assert "192.168.1.129" in hosts
    assert "192.168.1.127" not in hosts
    assert len(hosts) == 125


def test_recovery_caps_large_local_subnet() -> None:
    """A large adapter network is limited to the previous address's /24."""
    hosts = recovery_hosts("192.168.20.161", [_adapter("192.168.1.108", 16)])

    assert "192.168.20.162" in hosts
    assert "192.168.21.1" not in hosts
    assert len(hosts) == 253


def test_recovery_skips_unrelated_or_disabled_adapter() -> None:
    """Only an enabled adapter that owns the old address is scanned."""
    assert not recovery_hosts(
        "192.168.1.161",
        [
            _adapter("10.0.0.10", 24),
            _adapter("192.168.1.108", 24, enabled=False),
        ],
    )


def test_recovery_skips_invalid_or_ipv6_address() -> None:
    """Recovery only handles a valid IPv4 address."""
    adapters = [_adapter("192.168.1.108", 24)]

    assert not recovery_hosts("not-an-address", adapters)
    assert not recovery_hosts("2001:db8::1", adapters)
