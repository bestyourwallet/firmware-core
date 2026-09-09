from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator

    TokenInfoTuple = tuple[
        str,  # metadata address
        str,  # symbol
        int,  # decimals
    ]


class AptosTokenInfo:
    def __init__(
        self,
        metadata: str,
        symbol: str,
        decimals: int,
    ) -> None:
        self.metadata = metadata
        self.symbol = symbol
        self.decimals = decimals


def token_by_metadata(metadata: str):
    metadata = metadata.lower()
    for token_info in _token_iterator():
        if token_info[0] == metadata:
            return AptosTokenInfo(*token_info)
    return None


def _token_iterator() -> "Iterator[TokenInfoTuple]":
    yield (
        "0x357b0b74bc833e95a115ad22604854d6b0fca151cecd94111770e5d6ffc9dc2b",
        "USDt",
        6,
    )
    yield (
        "0xbae207659db88bea0cbead6da0ed00aac12edcdda169e591cd41c94180b46f3b",
        "USDC",
        6,
    )
