from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator

    TokenInfoTuple = tuple[
        str,  # account_id
        str,  # symbol
        int,  # decimals
    ]


def token_by_account(account_id: str) -> tuple[str, int] | None:
    for token_account_id, symbol, decimals in _token_iterator():
        if account_id == token_account_id:
            return symbol, decimals
    return None


def _token_iterator() -> "Iterator[TokenInfoTuple]":
    yield ("usdt.tether-token.near", "USDT", 6)
