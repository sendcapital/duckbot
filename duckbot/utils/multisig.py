from web3 import Web3

# Connect to the network
provider_url = 'https://network.ambrosus-test.io'
w3 = Web3(Web3.HTTPProvider(provider_url))

# Oracle ABI
oracle_abi = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "questionId", "type": "bytes32"},
            {"internalType": "bool", "name": "outcome", "type": "bool"}
        ],
        "name": "reportOutcome",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "questionId", "type": "bytes32"},
            {"internalType": "bool", "name": "originalOutcomeStood", "type": "bool"}
        ],
        "name": "resolveDispute",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

oracle_address = "0x501E90247c71146F195F6410Ba0f10bF63FB13C2"

def fetch_en_data(w3, question_id: str, outcome: bool): 
    try:
        oracle_contract = w3.eth.contract(address=oracle_address, abi=oracle_abi)
        # Encode function call
        data = oracle_contract.encode_abi("reportOutcome", args=[question_id, outcome])
        return data
    except Exception as e:
        print(f"Error: {e}")

# Example parameters
question_id = "0x77616435a5de1cbdba13641e96da6ce9505613082ee8769c2a4d32dcc268eb6c"
outcome = True

# Fetch and print the encoded data
result = fetch_en_data(w3, question_id, outcome)
print(result)