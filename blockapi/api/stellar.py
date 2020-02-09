from blockapi.services import (
    BlockchainAPI,
    on_failure_return_none
)


class StellarAPI(BlockchainAPI):
    """
    coins: stellar
    API docs: https://www.stellar.org/developers/horizon/reference/index.html
    Explorer: https://stellarchain.io/
    """

    active = True

    symbol = 'XLM'
    base_url = 'https://horizon.stellar.org'
    rate_limit = None
    coef = 1
    max_items_per_page = None
    page_offset_step = None
    confirmed_num = None

    supported_requests = {
        'get_balance': '/accounts/{address}',
    }

    @on_failure_return_none()
    def get_balance(self):
        response = self.request('get_balance',
                                address=self.address)
        if not response:
            return None

        #return response.get('balances')
        balances = [{ 'symbol': bal['asset_code'],
                      'amount': float(bal['balance']),
                    } for bal in response['balances'] if 'asset_code' in bal ]
        balance_XLM = [{ 'symbol': 'XLM',
                         'amount': float(bal['balance']),
                       } for bal in response['balances'] if bal['asset_type'] == 'native' ]

        return balances + balance_XLM
