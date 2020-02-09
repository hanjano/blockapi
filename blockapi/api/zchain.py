from blockapi.services import (
    BlockchainAPI,
    on_failure_return_none
)


class ZchainAPI(BlockchainAPI):
    """
    coins: zcash
    API docs: https://explorer.zcha.in/api
    Explorer: https://explorer.zcha.in/
    """

    active = True

    symbol = 'ZEC'
    base_url = 'https://api.zcha.in'
    rate_limit = None
    coef = 1
    max_items_per_page = None
    page_offset_step = None
    confirmed_num = None

    supported_requests = {
        'get_balance': '/v2/mainnet/accounts/{address}',
    }

    @on_failure_return_none()
    def get_balance(self):
        response = self.request('get_balance',
                                address=self.address)
        if not response:
            return None

        retval = response.get('balance') * self.coef
        return [{'symbol': self.symbol, 'amount': retval}]
