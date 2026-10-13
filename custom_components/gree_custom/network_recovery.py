"""Small helpers for local IP recovery."""

from collections.abc import Iterable, Mapping
from ipaddress import IPv4Address, ip_address, ip_network
from typing import Any

AUTO_RECOVERY_PREFIX = 24


def recovery_hosts(
    previous_ip: str, adapters: Iterable[Mapping[str, Any]]
) -> list[str]:
    """Return a bounded local subnet scan for a device's previous IP.

    Home Assistant may expose only the limited broadcast address when its
    default adapter is the only enabled adapter. Some Gree Wi-Fi modules do
    not answer that broadcast. Probe the matching local subnet with unicast
    packets instead. Networks larger than a /24 are capped to the /24 around
    the previous address, so one recovery cannot flood a large LAN.
    """
    try:
        target = ip_address(previous_ip)
    except ValueError:
        return []

    if not isinstance(target, IPv4Address):
        return []

    for adapter in adapters:
        if not adapter.get("enabled"):
            continue

        for ip_info in adapter.get("ipv4", []):
            try:
                adapter_network = ip_network(
                    f"{ip_info['address']}/{ip_info['network_prefix']}",
                    strict=False,
                )
            except (KeyError, TypeError, ValueError):
                continue

            if target not in adapter_network:
                continue

            prefix = max(adapter_network.prefixlen, AUTO_RECOVERY_PREFIX)
            recovery_network = ip_network(f"{target}/{prefix}", strict=False)
            return [
                str(host) for host in recovery_network.hosts() if host != target
            ]

    return []
