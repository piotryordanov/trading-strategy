"""Data structures and information about EVM based blockchains.

We embed the chain list data from https://github.com/ethereum-lists/chains as the submodule for the Python package.
"""

import os
import enum
import json
from typing import Optional, Dict

#: In-process cached chain data, so we do not need to hit FS every time we access
_chain_data: Dict[int, dict] = {}

#: Slug to chain id mapping
_slug_map: Dict[str, int] = {}


class ChainDataDoesNotExist(Exception):
    """Cannot find data for a specific chain"""


def _ensure_chain_data_lazy_init():

    global _chain_data
    global _slug_map

    if _chain_data:
        # Already initialized
        return

    for chain_id in ChainId:
        chain_id = chain_id.value
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "chains", "_data", "chains"))
        if not os.path.exists(path):
            raise RuntimeError(f"Chain data folder {path} not found. Make sure you have initialised git submodules or Python packaking is correct")

        data_file = os.path.join(path, f"eip155-{chain_id}.json")
        if not os.path.exists(data_file):
            raise ChainDataDoesNotExist(f"Chain data does not exist: {data_file}")

        _chain_data[chain_id] = json.load(open(data_file, "rt"))

        # Apply our own chain data records
        _chain_data[chain_id].update(_CHAIN_DATA_OVERRIDES.get(chain_id, {}))

    # Build slug -> chain id reverse mapping
    for chain_id, data in _chain_data.items():
        _slug_map[data["slug"]] = chain_id


def _get_chain_data(chain_id: int):
    _ensure_chain_data_lazy_init()
    return _chain_data[chain_id]


def _get_slug_map() -> Dict[str, int]:
    _ensure_chain_data_lazy_init()
    return _slug_map


class ChainId(enum.Enum):
    """Ethereum EVM chain ids and chain metadata.

    Chain id is an integer that defines the identity of a blockchain,
    all running on same or different EVM implementations.

    See https://chainid.network/ and https://github.com/ethereum-lists/chains for the full list.

    This class also provides various other metadata attributes besides `ChainId.value`, like `ChainId.get_slug()`.
    These are pulled from chaindata git submodule.
    """

    #: Ethereum mainnet chain id
    ethereum = 1

    #: Binance Smarrt Chain mainnet chain id
    bsc = 56

    #: Polygon chain id
    polygon = 137

    @property
    def data(self) -> dict:
        """Get chain data entry for this chain."""
        return _get_chain_data(self.value)

    def get_name(self) -> str:
        """Get full human readab name for this blockchain"""
        return self.data["name"]

    def get_slug(self) -> str:
        """Get URL slug for this chain"""
        return self.data["slug"]

    def get_homepage(self) -> str:
        """Get homepage link for this blockchain"""

        # TODO: Use chain id JSON data in the future
        return self.data["infoURL"]

    def get_svg_icon_link(self) -> str:
        """Get an absolute SVG image link to a chain icon, transparent background"""
        return self.data["svg_icon"]

    def get_explorer(self) -> str:
        """Get explorer landing page for this blockchain"""
        return self.data["explorers"][0]["url"]

    def get_address_link(self, address) -> str:
        """Get one address link.

        Use EIP3091 format.

        https://eips.ethereum.org/EIPS/eip-3091
        """
        return f"{self.get_explorer()}/address/{address}"

    def get_tx_link(self, tx) -> str:
        """Get one tx link"""
        return f"{self.get_explorer()}/tx/{tx}"

    @staticmethod
    def get_by_slug(slug: str) -> Optional["ChainId"]:
        """Map a slug back to the chain.

        Most useful for resolving URLs.
        """
        slug_map = _get_slug_map()
        chain_id_value = slug_map.get(slug)
        if chain_id_value is None:
            return None
        return ChainId(chain_id_value)


#: Override stuff we do not like in Chain data repo
#:
#: Arweave permaweb dropped
#: https://hv4gxzchk24cqfezebn3ujjz6oy2kbtztv5vghn6kpbkjc3vg4rq.arweave.net/PXhr5EdWuCgUmSBbuiU587GlBnmde1MdvlPCpIt1NyM/
#: with free AR from the faucet https://faucet.arweave.net/
#:
_CHAIN_DATA_OVERRIDES = {
    1: {
        "name": "Ethereum",
        "slug": "ethereum",
        "svg_icon": "https://upload.wikimedia.org/wikipedia/commons/0/05/Ethereum_logo_2014.svg",
    },

    # BSC
    56: {
        "name": "Binance Smart Chain",
        # Deployed on Arweave for good
        "slug": "binance",
        "svg_icon": "https://hv4gxzchk24cqfezebn3ujjz6oy2kbtztv5vghn6kpbkjc3vg4rq.arweave.net/fgp9wHyH92hION8E6CuPtUNbmiTlqsl23QbQlwA8cZQ",
    },

    # Polygon
    #
    137: {
        "name": "Polygon",
        "slug": "polygon",
        "svg_icon": "https://hv4gxzchk24cqfezebn3ujjz6oy2kbtztv5vghn6kpbkjc3vg4rq.arweave.net/nLW0IfMZnhhaqdN1AbzC4d1NLZSpBlIMEHhXq-KcOws",
    },

}

