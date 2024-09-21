from web3 import Web3

def fetch_eth_balance(w3, address: str): 
  checksum_address = w3.to_checksum_address(address)
  try:
    balance = w3.eth.get_balance(checksum_address)
    formatted_balance = w3.from_wei(balance, 'ether')
    return formatted_balance
  except Exception as e:
    return None