// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

contract GenericMultisigWallet {
    address[] public owners;
    uint public required;
    uint public transactionCount;

    struct Transaction {
        address to;
        uint value;
        bytes data;
        bool executed;
        uint approvalCount;
    }

    mapping(uint => Transaction) public transactions;
    mapping(uint => mapping(address => bool)) public approvals;

    event Deposit(address indexed sender, uint amount);
    event SubmitTransaction(address indexed owner, uint indexed txIndex, address indexed to, uint value, bytes data);
    event ApproveTransaction(address indexed owner, uint indexed txIndex);
    event ExecuteTransaction(address indexed owner, uint indexed txIndex);
    event ExecutionResult(uint indexed txIndex, bool success);

    constructor(address[] memory _owners, uint _required) {
        require(_owners.length > 0, "Owners required");
        require(_required > 0 && _required <= _owners.length, "Invalid required number of owners");

        for (uint i = 0; i < _owners.length; i++) {
            address owner = _owners[i];
            require(owner != address(0), "Invalid owner");
            owners.push(owner);
        }

        required = _required;
    }

    receive() external payable {
        emit Deposit(msg.sender, msg.value);
    }

    function submitTransaction(address _to, uint _value, bytes memory _data) public {
        require(isOwner(msg.sender), "Not owner");
        uint txIndex = transactionCount;

        transactions[txIndex] = Transaction({
            to: _to,
            value: _value,
            data: _data,
            executed: false,
            approvalCount: 0
        });

        transactionCount += 1;
        emit SubmitTransaction(msg.sender, txIndex, _to, _value, _data);
    }

    function approveTransaction(uint _txIndex) public {
        require(isOwner(msg.sender), "Not owner");
        require(_txIndex < transactionCount, "Invalid transaction");
        require(!approvals[_txIndex][msg.sender], "Transaction already approved");
        require(!transactions[_txIndex].executed, "Transaction already executed");

        approvals[_txIndex][msg.sender] = true;
        transactions[_txIndex].approvalCount += 1;

        emit ApproveTransaction(msg.sender, _txIndex);
    }

    function executeTransaction(uint _txIndex) public {
        require(isOwner(msg.sender), "Not owner");
        require(_txIndex < transactionCount, "Invalid transaction");
        require(!transactions[_txIndex].executed, "Transaction already executed");
        require(transactions[_txIndex].approvalCount >= required, "Not enough approvals");

        Transaction storage transaction = transactions[_txIndex];
        transaction.executed = true;

        (bool success, ) = transaction.to.call{value: transaction.value}(transaction.data);
        
        emit ExecuteTransaction(msg.sender, _txIndex);
        emit ExecutionResult(_txIndex, success);

        require(success, "Transaction execution failed");
    }

    function isOwner(address _address) public view returns (bool) {
        for (uint i = 0; i < owners.length; i++) {
            if (owners[i] == _address) {
                return true;
            }
        }
        return false;
    }
}