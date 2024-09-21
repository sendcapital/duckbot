// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IOracle {
    function getOutcome(bytes32 questionId) external view returns (bool, bool, bool);
    function getResolutionTimestamp(bytes32 questionId) external view returns (uint256);
}

contract PredictionMarket is ReentrancyGuard, Ownable {
    string public question;
    bytes32 public questionId;
    uint256 public endTime;
    address public oracleAddress;
    bool public isResolved;
    bool public outcome;

    uint256 public resolutionTime;
    uint256 public constant DISPUTE_PERIOD = 3 minutes;

    uint256 public MAX_PRICE;
    uint256 public oraclePrice;

    uint256 public totalYesAmount;
    uint256 public totalNoAmount;

    uint256 public nonce;

    address public settlerAddress;

    mapping(address => uint256) public yesBets;
    mapping(address => uint256) public noBets;
    mapping(address => bool) public hasClaimed;

    mapping(address => int256) public userBalance;
    mapping(address => int256) public userSize;
    mapping(address => int256) public userNotional;

    event MarketCreated(string question, uint256 endTime, address oracleAddress, uint256 maxPrice);
    event Deposit(address indexed user, int256 amount);
    event Withdrawal(address indexed user, int256 amount);
    event PositionUpdated(address indexed user, int256 newSize, int256 newNotional);
    event MarketSettled(address indexed user, int256 settledSize, int256 settledNotional);
    event MarketResolved(bool outcome, uint256 finalPrice);
    event AccountsMatched(address indexed maker, address indexed taker, int256 size, int256 notional, uint256 newNonce);

    event Debug(int256 uintNumber, int256 intNumber);

    constructor(
        string memory _question,
        uint256 _endTime,
        address _oracleAddress,
        uint256 _MAX_PRICE   
    ) Ownable(msg.sender) {
        question = _question;
        questionId = keccak256(abi.encodePacked(question));
        endTime = _endTime;
        oracleAddress = _oracleAddress;
        MAX_PRICE = _MAX_PRICE;
        nonce = 0;
        settlerAddress = address(this);

        emit MarketCreated(_question, _endTime, _oracleAddress, _MAX_PRICE);
    }

    function deposit() external payable {
        userBalance[msg.sender] += int256(msg.value);  // Cast msg.value to int256
        emit Deposit(msg.sender, int256(msg.value));   // Emit as int256
    }

    function withdraw(int256 amount) external nonReentrant {
        if (isResolved && userSize[msg.sender] != 0) {
            settleMarket(msg.sender);
        }

        uint256 userMargin = availableMargin(msg.sender);

        emit Debug(amount, amount);
        emit Debug(userBalance[msg.sender], int256(userMargin));

        
        // Convert userMargin (uint256) to int256 for the comparison
        require(userBalance[msg.sender] >= amount + int256(userMargin), "Insufficient funds");
        
        userBalance[msg.sender] -= amount; 
        
        (bool success, ) = payable(msg.sender).call{value: uint256(amount)}("");  // Ensure amount is cast to uint256 for transfer
        require(success, "ETH transfer failed");

        emit Withdrawal(msg.sender, amount);
    }


    function worstPNL(address userAddress) public view returns (int256 pnl) {
        int256 worstExitNotional = 0;
        if (userSize[userAddress] < 0) {
            worstExitNotional = int256(MAX_PRICE) * userSize[userAddress];
        }

        return worstExitNotional - int256(userNotional[userAddress]);
    }
    
    function availableMargin(address userAddress) public view returns (uint256 margin) {
        int256 balance = int256(userBalance[userAddress]);
        int256 pnl = worstPNL(userAddress);
        return uint256(balance + pnl);
    }
    
    function matchAccounts(address makerAddress, address takerAddress, int256 matchedMakerSize, int256 matchedMakerNotional, uint256 inputNonce) public onlyOwner {
        require(inputNonce == nonce + 1, "Incorrect nonce");

        userSize[makerAddress] -= matchedMakerSize;
        userNotional[makerAddress] -= matchedMakerNotional;

        require(int256(availableMargin(makerAddress)) >= 0 || makerAddress == settlerAddress, "Insufficient margin for maker");

        userSize[takerAddress] += matchedMakerSize;
        userNotional[takerAddress] += matchedMakerNotional;
        
        require(int256(availableMargin(takerAddress)) >= 0 || takerAddress == settlerAddress, "Insufficient margin for taker");

        nonce++;

        emit PositionUpdated(makerAddress, userSize[makerAddress], userNotional[makerAddress]);
        emit PositionUpdated(takerAddress, userSize[takerAddress], userNotional[takerAddress]);
        emit AccountsMatched(makerAddress, takerAddress, matchedMakerSize, matchedMakerNotional, nonce);
    }

    function settleMarket(address userAddress) internal {
        require(isResolved, "Market is not resolved yet");

        int256 matchedMakerSize = userSize[userAddress];
        
        // Convert oraclePrice (uint256) to int256 before multiplying it with matchedMakerSize
        int256 matchedMakerNotional = int256(oraclePrice) * (matchedMakerSize > 0 ? matchedMakerSize : -matchedMakerSize);
        
        // Call matchAccounts with the updated types and nonce increment
        matchAccounts(settlerAddress, userAddress, matchedMakerSize, matchedMakerNotional, nonce + 1);

        emit MarketSettled(userAddress, matchedMakerSize, matchedMakerNotional);
    }


    function resolveOracle(uint256 finalPrice) external onlyOwner {
        require(block.timestamp >= endTime, "Market has not ended yet");
        require(!isResolved, "Market already resolved");

        (bool _outcome, bool resolved, bool inDispute) = IOracle(oracleAddress).getOutcome(questionId);
        
        require(resolved, "Outcome not yet available from Oracle");
        require(!inDispute, "Outcome is currently under dispute");
        
        uint256 oracleResolutionTime = IOracle(oracleAddress).getResolutionTimestamp(questionId);
        require(block.timestamp > oracleResolutionTime + DISPUTE_PERIOD, "Dispute period not over");

        outcome = _outcome;
        oraclePrice = finalPrice; 
        isResolved = true;
        resolutionTime = block.timestamp;

        emit MarketResolved(outcome, finalPrice);
    }

    function getMarketInfo() external view returns (
        string memory _question,
        uint256 _endTime,
        bool _isResolved,
        bool _outcome,
        uint256 _totalYesAmount,
        uint256 _totalNoAmount
    ) {
        return (question, endTime, isResolved, outcome, totalYesAmount, totalNoAmount);
    }
}