from typing import TYPE_CHECKING

from trezor.lvglui.scrs import theme_path_default
from trezor.strings import format_amount

from . import ICON, PRIMARY_COLOR

if TYPE_CHECKING:
    from typing import Iterator

    # fmt: off
    NetworkInfoTuple = tuple[
        str,  # chain_id
        str,  # chain_name
        str,  # coin_denom
        str,  # coin_minimal_denom
        int,  # coin_decimals
        str,  # hrp
        str,  # icon
        int,  # primary_color
    ]
    TokenInfoTuple = tuple[
        str,  # denom
        str,  # symbol
        int,  # decimals
    ]
    # fmt: on


class NetworkInfo:
    def __init__(
        self,
        chainId: str,
        chainName: str,
        coinDenom: str,
        coinMinimalDenom: str,
        coinDecimals: int,
        hrp: str,
        icon: str,
        primary_color: int,
    ) -> None:
        self.chainId = chainId
        self.chainName = chainName
        self.coinDenom = coinDenom
        self.coinMinimalDenom = coinMinimalDenom
        self.coinDecimals = coinDecimals
        self.hrp = hrp
        self.icon = icon
        self.primary_color = primary_color


def getChainName(chainId: str) -> str | None:
    n = by_chain_id(chainId)
    if n is None:
        return None

    return n.chainName


def retrieve_theme_by_hrp(hrp: str | None) -> tuple[str, int, str]:
    if hrp:
        for _, chain_name, *_, _hrp, icon, primary_color in _networks_iterator():
            if hrp == _hrp:
                return (chain_name, primary_color, icon)
    return ("Cosmos", PRIMARY_COLOR, ICON)


def getChainHrp(chainId: str) -> str | None:
    n = by_chain_id(chainId)
    if n is None:
        return None

    return n.hrp


def formatAmont(chainId: str, amount: str, denom: str) -> str:
    n = by_chain_id(chainId)
    if n is None:
        token_info = token_by_chain_denom(chainId, denom)
        if token_info is not None:
            symbol, decimals = token_info
            return f"{format_amount(int(amount), decimals)} {symbol}"
        return f"{amount} {denom}"

    if denom == n.coinMinimalDenom:
        return f"{format_amount(int(amount), n.coinDecimals)} {n.coinDenom}"

    token_info = token_by_chain_denom(chainId, denom)
    if token_info is not None:
        symbol, decimals = token_info
        return f"{format_amount(int(amount), decimals)} {symbol}"

    return f"{amount} {denom}"


def token_by_chain_denom(chainId: str, denom: str) -> tuple[str, int] | None:
    for token_denom, symbol, decimals in _token_iterator(chainId):
        if denom == token_denom:
            return symbol, decimals
    return None


def _token_iterator(chainId: str) -> Iterator[TokenInfoTuple]:
    if chainId == "bbn-1":
        yield (
            "ibc/65D0BEC6DAD96C7F5043D1E54E54B6BB5D5B3AEC3FF6CEBB75B9E059F3580EA3",
            "USDC",
            6,
        )


def by_chain_id(chainId: str) -> NetworkInfo | None:
    for network_info in _networks_iterator():
        if network_info[0] == chainId:
            return NetworkInfo(*network_info)
    return None


def _networks_iterator() -> Iterator[NetworkInfoTuple]:
    yield (
        "cosmoshub-4",
        "Cosmos Hub",
        "ATOM",
        "uatom",
        6,
        "cosmos",
        # "A:/res/chain-atom.png",
        theme_path_default("chain_atom.png"),
        0x2D2F46,
    )
    yield (
        "osmosis-1",
        "Osmosis",
        "OSMO",
        "uosmo",
        6,
        "osmo",
        theme_path_default("chain_osmo.png"),
        0x4D4996,
    )
    yield (
        "secret-4",
        "Secret Network",
        "SCRT",
        "uscrt",
        6,
        "secret",
        theme_path_default("chain_scrt.png"),
        0x626B75,
    )
    yield (
        "akashnet-2",
        "Akash",
        "AKT",
        "uakt",
        6,
        "akash",
        theme_path_default("chain_akt.png"),
        0xFF414C,
    )
    yield (
        "crypto-org-chain-mainnet-1",
        "Crypto.org",
        "CRO",
        "basecro",
        8,
        "cro",
        theme_path_default("chain_cro.png"),
        0x0F50AB,
    )
    yield (
        "iov-mainnet-ibc",
        "Starname",
        "IOV",
        "uiov",
        6,
        "star",
        theme_path_default("chain_iov.png"),
        0x5C67B0,
    )
    yield (
        "sifchain-1",
        "Sifchain",
        "ROWAN",
        "rowan",
        18,
        "sif",
        theme_path_default("chain_rowan.png"),
        0xF9DB6C,
    )
    yield (
        "shentu-2.2",
        "Shentu",
        "CTK",
        "uctk",
        6,
        "certik",
        theme_path_default("chain_ctk.png"),
        0xE5AE4D,
    )
    yield (
        "irishub-1",
        "IRISnet",
        "IRIS",
        "uiris",
        6,
        "iaa",
        # "A:/res/chain-iris.png",
        theme_path_default("chain_iris.png"),
        0x4947BC,
    )
    yield (
        "regen-1",
        "Regen",
        "REGEN",
        "uregen",
        6,
        "regen",
        theme_path_default("chain_regen.png"),
        0x30A95B,
    )
    yield (
        "core-1",
        "Persistence",
        "XPRT",
        "uxprt",
        6,
        "persistence",
        theme_path_default("chain_xprt.png"),
        0xE50913,
    )
    yield (
        "sentinelhub-2",
        "Sentinel",
        "DVPN",
        "udvpn",
        6,
        "sent",
        theme_path_default("chain_dvpn.png"),
        0x0155FB,
    )
    yield (
        "ixo-4",
        "ixo",
        "IXO",
        "uixo",
        6,
        "ixo",
        theme_path_default("chain_ixo.png"),
        0x00D2FF,
    )
    yield (
        "emoney-3",
        "e-Money",
        "NGM",
        "ungm",
        6,
        "emoney",
        theme_path_default("chain_ngm.png"),
        0xCCF7EE,
    )
    yield (
        "agoric-3",
        "Agoric",
        "BLD",
        "ubld",
        6,
        "agoric",
        theme_path_default("chain_bld.png"),
        0xD73252,
    )
    yield (
        "bostrom",
        "Bostrom",
        "BOOT",
        "boot",
        0,
        "bostrom",
        theme_path_default("chain_boot.png"),
        0x00AF02,
    )
    yield (
        "juno-1",
        "Juno",
        "JUNO",
        "ujuno",
        6,
        "juno",
        theme_path_default("chain_juno.png"),
        0xFF7B7C,
    )
    yield (
        "stargaze-1",
        "Stargaze",
        "STARS",
        "ustars",
        6,
        "stars",
        theme_path_default("chain_stars.png"),
        0xDB2877,
    )
    yield (
        "axelar-dojo-1",
        "Axelar",
        "AXL",
        "uaxl",
        6,
        "axelar",
        theme_path_default("chain_axl.png"),
        0x54607C,
    )
    yield (
        "sommelier-3",
        "Sommelier",
        "SOMM",
        "usomm",
        6,
        "somm",
        theme_path_default("chain_somm.png"),
        0xF26057,
    )
    yield (
        "umee-1",
        "Umee",
        "UMEE",
        "uumee",
        6,
        "umee",
        theme_path_default("chain_umee.png"),
        0xDDB1FF,
    )
    yield (
        "gravity-bridge-3",
        "Gravity Bridge",
        "GRAV",
        "ugraviton",
        6,
        "gravity",
        theme_path_default("chain_grav.png"),
        0x2946B4,
    )
    yield (
        "tgrade-mainnet-1",
        "Tgrade",
        "TGD",
        "utgd",
        6,
        "tgrade",
        theme_path_default("chain_tgd.png"),
        0x4F5D87,
    )
    yield (
        "stride-1",
        "Stride",
        "STRD",
        "ustrd",
        6,
        "stride",
        theme_path_default("chain_strd.png"),
        0xE6007A,
    )
    yield (
        "evmos_9001-2",
        "Evmos",
        "EVMOS",
        "aevmos",
        18,
        "evmos",
        theme_path_default("chain_evmos.png"),
        0xEC4C32,
    )
    yield (
        "injective-1",
        "Injective",
        "INJ",
        "inj",
        18,
        "inj",
        theme_path_default("chain_ing.png"),
        0x01A8FC,
    )
    yield (
        "kava_2222-10",
        "Kava",
        "KAVA",
        "ukava",
        6,
        "kava",
        theme_path_default("chain_kava.png"),
        0xFF433E,
    )
    yield (
        "quicksilver-1",
        "Quicksilver",
        "QCK",
        "uqck",
        6,
        "quick",
        theme_path_default("chain_qck.png"),
        0x858585,
    )
    yield (
        "fetchhub-4",
        "Fetch.ai",
        "FET",
        "afet",
        18,
        "fetch",
        theme_path_default("chain_fet.png"),
        0x4C4CAE,
    )
    yield (
        "celestia",
        "Celestia",
        "TIA",
        "utia",
        6,
        "celestia",
        theme_path_default("chain_tia.png"),
        0x802EF4,
    )
    yield (
        "bbn-1",
        "Babylon",
        "BABY",
        "ubbn",
        6,
        "bbn",
        theme_path_default("chain_baby.png"),
        0xCF6533,
    )
    yield (
        "bbn-test-6",
        "Babylon Testnet",
        "BABY",
        "ubbn",
        6,
        "bbn",
        theme_path_default("chain_baby.png"),
        0xCF6533,
    )
    yield (
        "noble-1",
        "Noble",
        "USDC",
        "uusdc",
        6,
        "noble",
        theme_path_default("chain_noble.png"),
        0x41498D,
    )
