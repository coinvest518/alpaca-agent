import os
os.environ['COMPOSIO_API_KEY'] = 'ak_iorGi9iv2lBYAjAKUTpv'
from composio import Composio

composio = Composio()

# Check connected accounts
try:
    accounts = composio.connected_accounts.list()
    print('Connected accounts response:')
    print(f'Type: {type(accounts)}')

    # Try to iterate over it
    print('Iterating over accounts:')
    for account in accounts:
        print(f'Account: {account}')
        print(f'  Type: {type(account)}')
        if hasattr(account, 'id'):
            print(f'  ID: {account.id}')
        if hasattr(account, 'entity_id'):
            print(f'  Entity ID: {account.entity_id}')
        if hasattr(account, 'app_name'):
            print(f'  App: {account.app_name}')
        print()

except Exception as e:
    print('Error listing accounts:', e)