// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IOracle {
    function getOutcome(bytes32 questionId) external view returns (bool, bool, bool);
    function getResolutionTimestamp(bytes32 questionId) external view returns (uint256);
}

contract PredictionMarket is ReentrancyGuard, Ownable(msg.sender) {
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

    uint256 public userMargin;

    address public settlerAddress;

    mapping(address => uint256) public yesBets;
    mapping(address => uint256) public noBets;
    mapping(address => bool) public hasClaimed;

    mapping(address => uint256) public userBalance;
    mapping(address => uint256) public userSize;
    mapping(address => uint256) public userNotional;

    event BetPlaced(address bettor, bool isYes, uint256 amount);
    event MarketResolved(bool outcome);
    event PayoutClaimed(address recipient, uint256 amount);
    event PositionReduced(address bettor, bool isYes, uint256 amountReduced, uint256 payoutReceived);


    constructor(
        string memory _question,
        uint256 _endTime,
        address _oracleAddress,
        uint256 _MAX_PRICE   
    ) {
        question = _question;
        questionId = keccak256(abi.encodePacked(question));
        endTime = _endTime;
        oracleAddress = _oracleAddress;
        userBalance = 0;
        userSize = 0;
        userNotional = 0;
        MAX_PRICE = _MAX_PRICE;
    }

    // function increasePosition(bool isYes) external payable {
    //     require(block.timestamp < endTime, "Market has ended");
    //     require(!isResolved, "Market is resolved");
    //     require(msg.value > 0, "Bet amount must be greater than 0");

    //     if (isYes) {
    //         yesBets[msg.sender] += msg.value;
    //         totalYesAmount += msg.value;
    //     } else {
    //         noBets[msg.sender] += msg.value;
    //         totalNoAmount += msg.value;
    //     }

    //     emit BetPlaced(msg.sender, isYes, msg.value);
    // }

    // function reducePosition(bool isYes, uint256 reduceBet, uint256 payout) external nonReentrant {
    //     require(block.timestamp < endTime, "Market has ended");
    //     require(!isResolved, "Market is resolved");
    //     require(reduceBet > 0, "Reduction amount must be greater than 0");
    //     require(payout <= address(this).balance, "Insufficient contract balance");

    //     if (isYes) {
    //         require(yesBets[msg.sender] >= reduceBet, "Insufficient Yes position");
    //         yesBets[msg.sender] -= reduceBet;
    //         totalYesAmount -= reduceBet;
    //     } else {
    //         require(noBets[msg.sender] >= reduceBet, "Insufficient No position");
    //         noBets[msg.sender] -= reduceBet;
    //         totalNoAmount -= reduceBet;
    //     }

    //     // Transfer the calculated payout to the user
    //     (bool success, ) = msg.sender.call{value: payout}("");
    //     require(success, "ETH transfer failed");

    //     emit PositionReduced(msg.sender, isYes, reduceBet, payout);
    // }



    function deposit(uint256 amount) external payable {
        userBalance += amount; 
    }

    function withdraw(uint256 amount) external {
        if (isResolved && userSize(msg.sender) != 0) {
            settleMarket(msg.sender);
        }

        userMargin = availableMargin(msg.sender);
        userBalance -= amount; 
        
        require(userBalance >= userMargin, "Insufficient funds");
    }

    function worstPNL(address userAddress) external returns (uint256 pnl) {
        uint256 worstExitNotional = 0;
        if (userSize < 0) {
            worstExitNotional = MAX_PRICE * userSize(userAddress);
        }

        return worstExitNotional - userNotional(userAddress);
        
    }
    
    function availableMargin(address userAddress) external returns (uint256 margin) {
        return userBalance(userAddress) + worstPNL(userAddress);
    }

    
    function matchAccounts(address makerAddress, address takerAddress,  uint256 matchedMakerSize, uint256 matchedMakerNotional) external onlyOwner {
        
        userSize(makerAddress) -= matchedMakerSize;
        userNotional(makerAddress) -= matchedMakerNotional;

    
        require(availableMargin(makerAddress) >= 0 || makerAddress == settlerAddress, "");

        userSize(takerAddress) += matchedMakerSize;
        userNotional(takerAddress) += matchedMakerNotional;
        
        require(availableMargin(takerAddress) >= 0 || takerAddress == settlerAddress, "");

    }


    function settleMarket(address userAddress) internal {
        require(isResolved, "Market is not resolved yet");
        matchedMakerSize = userSize(userAddress);
        matchAccounts(settlerAddress, userAddress, matchedMakerSize, oraclePrice * matchedMakerSize);
    }

    // updated function name to resolveOracle
    // TODO: update the oraclePrice
    function resolveOracle() external {
        require(block.timestamp >= endTime, "Market has not ended yet");
        require(!isResolved, "Market already resolved");

        (bool _outcome, bool resolved, bool inDispute) = IOracle(oracleAddress).getOutcome(questionId);
        
        require(resolved, "Outcome not yet available from Oracle");
        require(!inDispute, "Outcome is currently under dispute");
        
        uint256 oracleResolutionTime = IOracle(oracleAddress).getResolutionTimestamp(questionId);
        require(block.timestamp > oracleResolutionTime + DISPUTE_PERIOD, "Dispute period not over");

        outcome = _outcome;
        isResolved = true;
        resolutionTime = block.timestamp;

        emit MarketResolved(outcome);
    }

    // // Allow users to claim the payouts
    // function claimPayouts(uint256 payoutAmount) external nonReentrant {
    //     require(isResolved, "Market not resolved");
    //     require(block.timestamp > resolutionTime + DISPUTE_PERIOD, "Dispute period not over");
    //     require(!hasClaimed[msg.sender], "Reward already claimed");

    //     require(payoutAmount <= totalYesAmount + totalNoAmount, "Payout exceeds total bets");
        
    //     hasClaimed[msg.sender] = true;
    //     (bool success, ) = msg.sender.call{value: payoutAmount}("");
    //     require(success, "ETH transfer failed");

    //     emit PayoutClaimed(msg.sender, payoutAmount);
    // }

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
