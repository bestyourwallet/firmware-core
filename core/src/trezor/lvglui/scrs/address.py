from typing import Any, Iterator

import storage.cache
from trezor import messages, utils, wire
from trezor.enums import InputScriptType, MessageType
from trezor.lvglui.scrs import lv, theme_path_default
from trezor.lvglui.scrs.template import ADDRESS_OFFLINE_RETURN_TYPE

from apps.workflow_handlers import find_registered_handler


class AddressManager:
    """Core logic for handling address generation and display"""

    class STATE:
        INIT = 0
        SHOW_ADDRESS = 1
        HANDLE_RESPONSE = 2
        UPDATE_ADDRESS = 3
        FINISH = 4
        ERROR = 5

    def __init__(self, name, index=0):
        self.current_handler = None
        self.current_chain_info = None
        self.btc_script_type = None
        self.use_standard_derivation = True
        self.user_interaction = None
        self.addr_type = None
        self.prev_session_id = None
        chain_info = self.get_chain_info(name)
        handler = find_registered_handler(None, chain_info["msg_type"])

        self.current_handler = handler
        self.current_chain_info = chain_info
        self.current_index = index

    # def init_chain_byname(self, name, index=0):

    def get_chain_info(self, name) -> dict:
        """Get chain configuration information"""
        for info in _chains_config_iterator():
            if info["name"] == name:
                return info
        raise wire.DataError("Chain info not found")

    def _prepare_btc_message(self):
        """Prepare Bitcoin message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        if self.btc_script_type == InputScriptType.SPENDP2SHWITNESS:
            path = self.current_chain_info["nested_segwit_path"][:]
            self.addr_type = "Nested Segwit"
        elif self.btc_script_type == InputScriptType.SPENDTAPROOT:
            path = self.current_chain_info["taproot_path"][:]
            self.addr_type = "Taproot"
        elif self.btc_script_type == InputScriptType.SPENDWITNESS:
            path = self.current_chain_info["native_segwit_path"][:]
            self.addr_type = "Native Segwit"
        elif self.btc_script_type == InputScriptType.SPENDADDRESS:
            path = self.current_chain_info["legacy_path"][:]
            self.addr_type = "Legacy"
        else:
            self.btc_script_type = InputScriptType.SPENDTAPROOT
            path = self.current_chain_info["taproot_path"][:]
            self.addr_type = "Taproot"
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(
            address_n=path, show_display=False, script_type=self.btc_script_type
        )

    def _prepare_eth_message(self):
        """Prepare Ethereum message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        if self.use_standard_derivation is True:
            pos = self.current_chain_info["index_pos"]
            self.addr_type = "BIP44 Standard"
        else:
            pos = self.current_chain_info["ledger_pos"]
            self.addr_type = "Ledger Live"
        path[pos] += self.current_index
        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False)

    def _prepare_sol_message(self):
        """Prepare Solana message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        if self.use_standard_derivation is True:
            path = self.current_chain_info["base_path"][:]
            pos = self.current_chain_info["index_pos"]
            self.addr_type = "BIP44 Standard"
        else:
            path = self.current_chain_info["ledger_path"][:]
            pos = self.current_chain_info["ledger_pos"]
            self.addr_type = "Ledger Live"
        path[pos] += self.current_index
        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False)

    def _prepare_ada_message(self):
        """Prepare Cardano message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        staking_path = self.current_chain_info["staking_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        staking_path[pos] += self.current_index
        self.addr_type = "BIP44 Standard"

        from trezor.messages import CardanoAddressParametersType
        from trezor.enums import CardanoDerivationType, CardanoAddressType

        address_parameters = CardanoAddressParametersType(
            address_type=CardanoAddressType.BASE,
            address_n=path,
            address_n_staking=staking_path,
        )
        derivation_type = CardanoDerivationType.ICARUS

        storage.cache.end_current_session()
        self.prev_session_id = storage.cache.get_session_id()
        self.curr_session_id = storage.cache.start_session()
        storage.cache.SESSION_DIRIVE_CARDANO = True

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(
            show_display=False,
            protocol_magic=764824073,
            network_id=1,
            address_parameters=address_parameters,
            derivation_type=derivation_type,
        )

    def _prepare_dot_message(self):
        """Prepare Polkadot message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "BIP44 Standard"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(
            address_n=path, show_display=False, network="polkadot", prefix=0
        )

    def _prepare_ckb_message(self):
        """Prepare Nervos message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "BIP44 Standard"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False, network="ckb")

    def _prepare_alephium_message(self):
        """Prepare Alephium message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "BIP44 Standard"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False, target_group=0)

    def _prepare_nexa_message(self):
        """Prepare Nexa message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "BIP44 Standard"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False, prefix="nexa")

    def _prepare_doge_message(self):
        """Prepare Dogecoin message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["legacy_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "Legacy"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False, coin_name="Dogecoin")

    def _prepare_bch_message(self):
        """Prepare Bitcoin Cash message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["legacy_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "Legacy"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False, coin_name="Bcash")

    def _prepare_xna_message(self):
        """Prepare Neurai message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["legacy_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "Legacy"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False, coin_name="Neurai")

    def _prepare_ltc_message(self):
        """Prepare Litecoin message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        if self.btc_script_type == InputScriptType.SPENDP2SHWITNESS:
            path = self.current_chain_info["nested_segwit_path"][:]
            self.addr_type = "Nested Segwit"
        elif self.btc_script_type == InputScriptType.SPENDWITNESS:
            path = self.current_chain_info["native_segwit_path"][:]
            self.addr_type = "Native Segwit"
        elif self.btc_script_type == InputScriptType.SPENDADDRESS:
            path = self.current_chain_info["legacy_path"][:]
            self.addr_type = "Legacy"
        else:
            self.btc_script_type = InputScriptType.SPENDP2SHWITNESS
            path = self.current_chain_info["nested_segwit_path"][:]
            self.addr_type = "Nested Segwit"
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(
            address_n=path,
            show_display=False,
            coin_name="Litecoin",
            script_type=self.btc_script_type,
        )

    def _prepare_kaspa_message(self):
        """Prepare Kaspa message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")
        from trezor.lvglui.i18n import gettext as _, keys as i18n_keys

        if self.use_standard_derivation is True:
            path = self.current_chain_info["base_path"][:]
            self.addr_type = _(i18n_keys.BUTTON_UKEY_EXTENDED)
        else:
            path = self.current_chain_info["base_path"][:]
            self.addr_type = _(i18n_keys.BUTTON_KASPA_OFFICIAL)

        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(
            address_n=path, show_display=False, use_tweak=self.use_standard_derivation
        )

    def _prepare_default_message(self):
        """Prepare default chain message"""
        if self.current_chain_info is None:
            raise wire.DataError("Chain info is None")

        path = self.current_chain_info["base_path"][:]
        pos = self.current_chain_info["index_pos"]
        path[pos] += self.current_index
        self.addr_type = "BIP44 Standard"

        msg_class = getattr(messages, self.current_chain_info["msg_class"])
        return msg_class(address_n=path, show_display=False)

    def _prepare_chain_message(self, name):
        """Prepare message object based on chain type"""

        if name == "Bitcoin":
            return self._prepare_btc_message()
        elif name == "Ethereum":
            return self._prepare_eth_message()
        elif name == "Solana":
            return self._prepare_sol_message()
        elif name == "Cardano":
            return self._prepare_ada_message()
        elif name.startswith("Polkadot"):
            return self._prepare_dot_message()
        elif name == "Nervos":
            return self._prepare_ckb_message()
        elif name == "Alephium":
            return self._prepare_alephium_message()
        elif name == "Dogecoin":
            return self._prepare_doge_message()
        elif name == "Litecoin":
            return self._prepare_ltc_message()
        elif name == "Neurai":
            return self._prepare_xna_message()
        elif name == "Bitcoin Cash":
            return self._prepare_bch_message()
        elif name == "Kaspa":
            return self._prepare_kaspa_message()
        else:
            return self._prepare_default_message()

    async def chain_address(self, ctx=wire.DUMMY_CONTEXT):
        chain_info = self.current_chain_info
        handler = self.current_handler
        if chain_info is None or handler is None:
            raise wire.DataError("Address manager is not initialized")

        msg = self._prepare_chain_message(chain_info["name"])
        try:
            address_resp: Any = await handler(ctx, msg)
        except Exception as e:
            if __debug__:
                import sys

                sys.print_exception(e)  # type: ignore["print_exception" is not a known member of module]
            # state = self.STATE.ERROR
            return

        ctx.primary_color = lv.color_hex(chain_info["primary_color"])
        ctx.icon_path = theme_path_default(f"{chain_info['icon']}-40.png")

        if utils.BITCOIN_ONLY:
            address = address_resp.address
        else:
            address = (
                address_resp.address
                if chain_info["msg_type"] != MessageType.NostrGetPublicKey
                else address_resp.npub
            )
        return address

    async def generate_address(self, name, index=0, ctx=wire.DUMMY_CONTEXT):
        """Main logic for generating addresses"""

        state = self.STATE.INIT
        chain_info = None

        while state not in (self.STATE.FINISH, self.STATE.ERROR):
            # pyright: off
            if state == self.STATE.INIT:
                chain_info = self.get_chain_info(name)
                handler = find_registered_handler(None, chain_info["msg_type"])

                self.current_handler = handler
                self.current_chain_info = chain_info

                state = self.STATE.SHOW_ADDRESS
                # await loop.sleep(100)

            elif state == self.STATE.SHOW_ADDRESS:
                if chain_info is None or self.current_handler is None:
                    state = self.STATE.ERROR
                    continue
                # Generate message
                msg = self._prepare_chain_message(chain_info["name"])
                try:
                    await self.current_handler(ctx, msg)
                except Exception as e:
                    if __debug__:
                        import sys

                        sys.print_exception(e)  # type: ignore["print_exception" is not a known member of module]
                    state = self.STATE.ERROR
                    continue

                current_chain_info = self.current_chain_info
                if current_chain_info is None:
                    state = self.STATE.ERROR
                    continue
                ctx.primary_color = lv.color_hex(current_chain_info["primary_color"])
                ctx.icon_path = theme_path_default(
                    f"{current_chain_info['icon']}-40.png"
                )

                # if utils.BITCOIN_ONLY:
                #     address = (
                #         address_resp.address
                #     )
                # else:
                #     address = (
                #         address_resp.address
                #         if chain_info["msg_type"] != MessageType.NostrGetPublicKey
                #         else address_resp.npub
                #     )

                # self.user_interaction = await show_address_offline(
                #     ctx,
                #     address=address,
                #     network=self.current_chain_info["name"],
                #     addr_type=self.addr_type,
                #     account_name=f" Account #{self.current_index + 1}",
                # )
                state = self.STATE.HANDLE_RESPONSE

            elif state == self.STATE.HANDLE_RESPONSE:
                # Handle user interaction results
                # state = self.STATE.FINISH
                # loop.sleep(1000)
                if isinstance(self.user_interaction, tuple):
                    return_type, value = self.user_interaction
                    if (
                        return_type
                        == ADDRESS_OFFLINE_RETURN_TYPE.COMMON_DRI_CONFIG_CHANGED
                    ):
                        self.use_standard_derivation = value
                        state = self.STATE.SHOW_ADDRESS
                    elif (
                        return_type
                        == ADDRESS_OFFLINE_RETURN_TYPE.BTC_DRI_CONFIG_CHANGED
                    ):
                        self.btc_script_type = value
                        state = self.STATE.SHOW_ADDRESS
                elif self.user_interaction == ADDRESS_OFFLINE_RETURN_TYPE.DONE:
                    state = self.STATE.FINISH
                else:
                    state = self.STATE.ERROR
            # pyright: on

        # Clean up
        self.cleanup()

    def cleanup(self):
        """Clean up state"""
        self.current_handler = None
        self.current_chain_info = None
        self.user_interaction = None
        self.addr_type = None
        self.current_index = 0
        self.btc_script_type = None
        self.use_standard_derivation = True
        self.addr_type = None
        storage.cache.SESSION_DIRIVE_CARDANO = False


def chains_brief_info() -> list[tuple[str, str]]:
    return [(chain["name"], chain["icon"]) for chain in _chains_config_iterator()]


def _chains_config_iterator() -> Iterator[dict]:

    yield {
        "msg_type": MessageType.GetAddress,
        "symbol": " BTC",
        "name": "Bitcoin",
        "msg_class": "GetAddress",
        "index_pos": -3,
        "legacy_path": [0x80000000 + 44, 0x80000000 + 0, 0x80000000 + 0, 0, 0],
        "native_segwit_path": [
            0x80000000 + 84,
            0x80000000 + 0,
            0x80000000 + 0,
            0,
            0,
        ],
        "nested_segwit_path": [
            0x80000000 + 49,
            0x80000000 + 0,
            0x80000000 + 0,
            0,
            0,
        ],
        "taproot_path": [0x80000000 + 86, 0x80000000 + 0, 0x80000000 + 0, 0, 0],
        "icon": "btc_btc",
        "primary_color": 0xFF9C00,
    }
    if utils.BITCOIN_ONLY:
        return
    yield {
        "msg_type": MessageType.EthereumGetAddressUKey,
        "symbol": " ETH",
        "name": "Ethereum",
        "msg_class": "EthereumGetAddressUKey",
        "index_pos": -1,
        "ledger_pos": -3,
        "base_path": [0x80000000 + 44, 0x80000000 + 60, 0x80000000 + 0, 0, 0],
        "icon": "evm_eth",
        "primary_color": 0x637FFF,
    }
    yield {
        "msg_type": MessageType.SolanaGetAddress,
        "symbol": " SOL",
        "name": "Solana",
        "msg_class": "SolanaGetAddress",
        "index_pos": -2,
        "ledger_pos": -1,
        "base_path": [
            0x80000000 + 44,
            0x80000000 + 501,
            0x80000000 + 0,
            0x80000000 + 0,
        ],
        "ledger_path": [0x80000000 + 44, 0x80000000 + 501, 0x80000000 + 0],
        "icon": "sol",
        "primary_color": 0xC74AE3,
    }
    yield {
        "msg_type": MessageType.TronGetAddress,
        "symbol": " TRX",
        "name": "Tron",
        "msg_class": "TronGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 195, 0x80000000 + 0, 0, 0],
        "icon": "tron",
        "primary_color": 0xFF0013,
    }
    yield {
        "msg_type": MessageType.TonGetAddress,
        "symbol": " TON",
        "name": "TON",
        "msg_class": "TonGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 607, 0x80000000 + 0],
        "icon": "ton",
        "primary_color": 0x0098EA,
    }
    yield {
        "msg_type": MessageType.KaspaGetAddress,
        "symbol": " KAS",
        "name": "Kaspa",
        "msg_class": "KaspaGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 111111, 0x80000000 + 0, 0, 0],
        "icon": "kaspa",
        "primary_color": 0x55ECC7,
    }
    yield {
        "msg_type": MessageType.SuiGetAddress,
        "symbol": " SUI",
        "name": "Sui",
        "msg_class": "SuiGetAddress",
        "index_pos": -3,
        "base_path": [
            0x80000000 + 44,
            0x80000000 + 784,
            0x80000000 + 0,
            0x80000000 + 0,
            0x80000000 + 0,
        ],
        "icon": "sui",
        "primary_color": 0x6FBCF0,
    }
    yield {
        "msg_type": MessageType.GetAddress,
        "symbol": " DOGE",
        "name": "Dogecoin",
        "msg_class": "GetAddress",
        "index_pos": -3,
        "legacy_path": [0x80000000 + 44, 0x80000000 + 3, 0x80000000 + 0, 0, 0],
        "icon": "btc_doge",
        "primary_color": 0xFF9C00,
    }
    yield {
        "msg_type": MessageType.CardanoGetAddress,
        "symbol": " ADA",
        "name": "Cardano",
        "msg_class": "CardanoGetAddress",
        "index_pos": -3,
        "base_path": [0x80000000 + 1852, 0x80000000 + 1815, 0x80000000 + 0, 0, 0],
        "staking_path": [
            0x80000000 + 1852,
            0x80000000 + 1815,
            0x80000000 + 0,
            2,
            0,
        ],
        "protocol_magic": 764824073,
        "network_id": 1,
        "icon": "ada",
        "primary_color": 0x2970FF,
    }
    yield {
        "msg_type": MessageType.RippleGetAddress,
        "symbol": " XRP",
        "name": "Ripple",
        "msg_class": "RippleGetAddress",
        "index_pos": -3,
        "base_path": [0x80000000 + 44, 0x80000000 + 144, 0x80000000 + 0, 0, 0],
        "icon": "xrp",
        "primary_color": 0x255770,
    }
    yield {
        "msg_type": MessageType.AptosGetAddress,
        "symbol": " APT",
        "name": "Aptos",
        "msg_class": "AptosGetAddress",
        "index_pos": -3,
        "base_path": [
            0x80000000 + 44,
            0x80000000 + 637,
            0x80000000 + 0,
            0x80000000 + 0,
            0x80000000 + 0,
        ],
        "icon": "apt",
        "primary_color": 0x255770,
    }
    # yield {
    #     "msg_type": MessageType.AlephiumGetAddress,
    #     "symbol": " ALPH",
    #     "name": "Alephium",
    #     "msg_class": "AlephiumGetAddress",
    #     "index_pos": -3,
    #     "base_path": [0x80000000 + 44, 0x80000000 + 1234, 0x80000000 + 0, 0, 0],
    #     "icon":"alephium",
    #     "primary_color": 0x255770,
    # }
    yield {
        "msg_type": MessageType.AlgorandGetAddress,
        "symbol": " ALGO",
        "name": "Algorand",
        "msg_class": "AlgorandGetAddress",
        "index_pos": -1,
        "base_path": [
            0x80000000 + 44,
            0x80000000 + 283,
            0x80000000 + 0,
            0x80000000 + 0,
            0x80000000 + 0,
        ],
        "icon": "algo",
        "primary_color": 0x255770,
    }
    # yield {
    #     "msg_type": MessageType.BenfenGetAddress,
    #     "symbol": " BENFEN",
    #     "name": "Benfen",
    #     "msg_class": "BenfenGetAddress",
    #     "index_pos": -3,
    #     "base_path": [
    #         0x80000000 + 44,
    #         0x80000000 + 728,
    #         0x80000000 + 0,
    #         0x80000000 + 0,
    #         0x80000000 + 0,
    #     ],
    #     "icon":"benfen",
    #     "primary_color": 0xCD4937,
    # }
    yield {
        "msg_type": MessageType.GetAddress,
        "symbol": " BCH",
        "name": "Bitcoin Cash",
        "msg_class": "GetAddress",
        "index_pos": -3,
        "legacy_path": [0x80000000 + 44, 0x80000000 + 145, 0x80000000 + 0, 0, 0],
        "icon": "btc_bch",
        "primary_color": 0x0AC18E,
    }
    yield {
        "msg_type": MessageType.ConfluxGetAddress,
        "symbol": " CFX",
        "name": "Conflux",
        "msg_class": "ConfluxGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 503, 0x80000000 + 0, 0, 0],
        "icon": "cfx",
        "primary_color": 0x255770,
    }
    yield {
        "msg_type": MessageType.CosmosGetAddress,
        "symbol": " ATOM",
        "name": "Cosmos",
        "msg_class": "CosmosGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 118, 0x80000000 + 0, 0, 0],
        "icon": "atom",
        "primary_color": 0x255770,
    }
    yield {
        "msg_type": MessageType.FilecoinGetAddress,
        "symbol": " FIL",
        "name": "Filecoin",
        "msg_class": "FilecoinGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 461, 0x80000000 + 0, 0, 0],
        "icon": "fil",
        "primary_color": 0x0090FF,
    }
    yield {
        "msg_type": MessageType.GetAddress,
        "symbol": " LTC",
        "name": "Litecoin",
        "msg_class": "GetAddress",
        "index_pos": -3,
        "legacy_path": [0x80000000 + 44, 0x80000000 + 2, 0x80000000 + 0, 0, 0],
        "native_segwit_path": [
            0x80000000 + 84,
            0x80000000 + 2,
            0x80000000 + 0,
            0,
            0,
        ],
        "nested_segwit_path": [
            0x80000000 + 49,
            0x80000000 + 2,
            0x80000000 + 0,
            0,
            0,
        ],
        "icon": "btc_ltc",
        "primary_color": 0x3683F7,
    }
    yield {
        "msg_type": MessageType.NearGetAddress,
        "symbol": " NEAR",
        "name": "NEAR",
        "msg_class": "NearGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 397, 0x80000000 + 0],
        "icon": "near",
        "primary_color": 0x255770,
    }
    yield {
        "msg_type": MessageType.NervosGetAddress,
        "symbol": " CKB",
        "name": "Nervos",
        "msg_class": "NervosGetAddress",
        "index_pos": -1,
        "base_path": [0x80000000 + 44, 0x80000000 + 309, 0x80000000 + 0, 0, 0],
        "icon": "nervos",
        "primary_color": 0x255770,
    }
    # yield {
    #     "msg_type": MessageType.NeoGetAddress,
    #     "symbol": " NEO",
    #     "name": "Neo N3",
    #     "msg_class": "NeoGetAddress",
    #     "index_pos": -1,
    #     "base_path": [0x80000000 + 44, 0x80000000 + 888, 0x80000000 + 0, 0, 0],
    #     "icon":"neo",
    #     "primary_color": 0x06CCAB,
    # }
    # yield {
    #     "msg_type": MessageType.GetAddress,
    #     "symbol": " NEUR",
    #     "name": "Neurai",
    #     "msg_class": "GetAddress",
    #     "index_pos": -3,
    #     "legacy_path": [0x80000000 + 44, 0x80000000 + 1900, 0x80000000 + 0, 0, 0],
    #     "icon":"btc_xna",
    #     "primary_color": 0x793EAA,
    # }
    # yield {
    #     "msg_type": MessageType.NexaGetAddress,
    #     "symbol": " NEXA",
    #     "name": "Nexa",
    #     "msg_class": "NexaGetAddress",
    #     "index_pos": -3,
    #     "base_path": [0x80000000 + 44, 0x80000000 + 29223, 0x80000000 + 0, 0, 0],
    #     "icon":"nexa",
    #     "primary_color": 0xFFE144,
    # }
    # yield {
    #     "msg_type": MessageType.NostrGetPublicKey,
    #     "symbol": " NOSTR",
    #     "name": "Nostr",
    #     "msg_class": "NostrGetPublicKey",
    #     "index_pos": -3,
    #     "base_path": [0x80000000 + 44, 0x80000000 + 1237, 0x80000000 + 0, 0, 0],
    #     "icon":"nostr",
    #     "primary_color": 0x8D45DD,
    # }
    yield {
        "msg_type": MessageType.PolkadotGetAddress,
        "symbol": " DOT",
        "name": "Polkadot AssetHub",
        "msg_class": "PolkadotGetAddress",
        "index_pos": -3,
        "base_path": [
            0x80000000 + 44,
            0x80000000 + 354,
            0x80000000 + 0,
            0x80000000 + 0,
            0x80000000 + 0,
        ],
        "icon": "dot",
        "primary_color": 0xE6007A,
    }
    # yield {
    #     "msg_type": MessageType.ScdoGetAddress,
    #     "symbol": " SCDO",
    #     "name": "SCDO",
    #     "msg_class": "ScdoGetAddress",
    #     "index_pos": -3,
    #     "base_path": [0x80000000 + 44, 0x80000000 + 541, 0x80000000 + 0, 0, 0],
    #     "icon":"scdo",
    #     "primary_color": 0x255770,
    # }
