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

oracle_address = "0x3A0d54AE4d623De4c345b13eE95B9C7b51318b64"

def fetch_en_data(w3, question_id: str, outcome: bool): 
    try:
        oracle_contract = w3.eth.contract(address=oracle_address, abi=oracle_abi)
        # Encode function call
        data = oracle_contract.encode_abi("reportOutcome", args=[question_id, outcome])
        return data
    except Exception as e:
        print(f"Error: {e}")

# Example parameters
question_id = "0x8fe65c1ff96f6bd9a6f91fdf7c7911063867b67667a5127cd7c015cc4233d1f4"
outcome = True

# Fetch and print the encoded data
result = fetch_en_data(w3, question_id, outcome)
print(result)