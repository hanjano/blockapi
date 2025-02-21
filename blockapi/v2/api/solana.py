import json
from typing import Dict, Iterable, Optional

from requests import Response

from blockapi.v2.base import (
    ApiException,
    ApiOptions,
    BlockchainApi,
    IBalance,
    InvalidAddressException,
)
from blockapi.v2.coins import COIN_SOL
from blockapi.v2.models import BalanceItem, Blockchain, Coin, CoinInfo


class SolanaApi(BlockchainApi, IBalance):
    """
    Solana RPC
    API docs: https://docs.solana.com/apps/jsonrpc-api
    """

    coin = COIN_SOL
    api_options = ApiOptions(
        blockchain=Blockchain.SOLANA,
        base_url='https://api.mainnet-beta.solana.com/',
        start_offset=0,
        max_items_per_page=1000,
        page_offset_step=1,
    )

    # API uses post requests
    supported_requests = {}

    token_program_id = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
    _tokens_map: Optional[Dict[str, Dict]] = None

    @property
    def tokens_map(self) -> Dict[str, Dict]:
        if self._tokens_map is None:
            response = self._session.get(
                'https://raw.githubusercontent.com/solana-labs/token-list/'
                'main/src/tokens/solana.tokenlist.json'
            )
            token_list = response.json()
            self._tokens_map = {t['address']: t for t in token_list['tokens']}

        return self._tokens_map

    def get_balance(self, address: str):
        balances = []

        sol_balance = self._get_sol_balance(address)
        if sol_balance is not None:
            balances.append(sol_balance)

        token_balances = list(self._yield_token_balances(address))
        if token_balances:
            balances.extend(token_balances)

        return balances

    def _get_sol_balance(
        self,
        address: str,
    ) -> Optional[BalanceItem]:
        response = self._request(method='getBalance', params=[address])
        if int(response['result']['value']) == 0:
            return

        return BalanceItem.from_api(
            balance_raw=response['result']['value'],
            coin=self.coin,
            last_updated=None,
            raw=response,
        )

    def _yield_token_balances(self, address: str) -> Iterable[BalanceItem]:
        response = self._request(
            method='getTokenAccountsByOwner',
            params=[
                address,
                {'programId': self.token_program_id},
                {'encoding': 'jsonParsed'},
            ],
        )

        for raw_balance in response['result']['value']:
            balance = self._parse_token_balance(raw_balance)
            if balance is not None:
                yield balance

    def _parse_token_balance(self, raw: Dict) -> Optional[BalanceItem]:
        info = raw['account']['data']['parsed']['info']
        if int(info['tokenAmount']['amount']) == 0:
            return

        address = info['mint']

        if address in self.tokens_map:
            token = self._get_token_data(address)
        else:
            token = Coin.from_api(
                blockchain=Blockchain.SOLANA,
                decimals=info['tokenAmount']['decimals'],
                address=address,
            )

        return BalanceItem.from_api(
            balance_raw=info['tokenAmount']['amount'],
            coin=token,
            raw=raw,
        )

    def _get_token_data(self, address: str) -> Coin:
        raw_token = self.tokens_map[address]
        extensions = raw_token.get('extensions', {})

        return Coin(
            symbol=raw_token['symbol'],
            name=raw_token['name'],
            decimals=raw_token['decimals'],
            blockchain=Blockchain.SOLANA,
            address=address,
            standards=['SPL'],
            info=CoinInfo.from_api(
                tags=raw_token.get('tags'),
                logo_url=raw_token.get('logoURI'),
                coingecko_id=extensions.get('coingeckoId'),
                website=extensions.get('website'),
            ),
        )

    def _request(self, method, params):
        body = json.dumps(
            {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params}
        )
        return self.post(body=body, headers={'Content-Type': 'application/json'})

    def _opt_raise_on_other_error(self, response: Response) -> None:
        json_response = response.json()
        if 'error' not in json_response:
            return

        if 'Invalid param' in json_response['error']['message']:
            raise InvalidAddressException(f'Invalid address format.')
        else:
            raise ApiException(json_response['error']['message'])
