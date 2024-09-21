// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IOracle {
    function getOutcome(
        bytes32 questionId
    ) external view returns (bool, bool, bool);

    function getResolutionTimestamp(
        bytes32 questionId
    ) external view returns (uint256);
}

contract PredictionMarket is ReentrancyGuard, Ownable {
    bytes32 public questionId;
    string public question;
    address public oracleAddress;
    uint256 public endTime;

    uint256 public resolutionTime;
    uint256 public constant DISPUTE_PERIOD = 3 minutes;

    int256 public matchNonce;

    bool public isResolved;
    bool public outcome;

    int256 public MAX_PRICE_E9 = 1_000_000_000;

    address public settlerAddress;

    mapping(address => int256) public userBalanceE18;
    mapping(address => int256) public userSizeE9;
    mapping(address => int256) public userNotionalE18;

    event MarketCreated(
        string question,
        uint256 endTime,
        address oracleAddress
    );
    event Deposit(address indexed user, uint256 amountE18);
    event Withdrawal(address indexed user, uint256 amountE18);
    event PositionUpdated(
        address indexed user,
        int256 newSizeE9,
        int256 newNotionalE18
    );
    event MarketSettled(
        address indexed user,
        int256 settledSizeE9,
        int256 settledNotionalE18
    );
    event MarketResolved(bool outcome);
    event AccountsMatched(
        address indexed maker,
        address indexed taker,
        int256 sizeE9,
        int256 notionalE18,
        int256 newNonce
    );

    constructor(
        string memory _question,
        uint256 _endTime,
        address _oracleAddress
    ) Ownable(msg.sender) {
        question = _question;
        questionId = keccak256(abi.encodePacked(question));
        endTime = _endTime;
        oracleAddress = _oracleAddress;
        matchNonce = 0;
        settlerAddress = address(this);

        emit MarketCreated(_question, _endTime, _oracleAddress);
    }

    function deposit() external payable {
        userBalanceE18[msg.sender] += int256(msg.value); // Cast msg.value to int256
        emit Deposit(msg.sender, msg.value);
    }

    function withdraw(uint256 amountE18) external nonReentrant {
        if (isResolved && userSizeE9[msg.sender] != 0) settleMarket(msg.sender);

        userBalanceE18[msg.sender] -= int256(amountE18);
        require(0 <= availableMarginE18(msg.sender), "Insufficient funds");

        (bool success, ) = payable(msg.sender).call{value: amountE18}("");
        require(success, "ETH transfer failed");

        emit Withdrawal(msg.sender, amountE18);
    }

    function worstPnlE18(address userAddress) public view returns (int256 pnl) {
        int256 worstExitNotionalE18 = 0;
        if (userSizeE9[userAddress] < 0)
            worstExitNotionalE18 = MAX_PRICE_E9 * userSizeE9[userAddress];

        return worstExitNotionalE18 - userNotionalE18[userAddress];
    }

    function availableMarginE18(
        address userAddress
    ) public view returns (int256 margin) {
        return userBalanceE18[userAddress] + worstPnlE18(userAddress);
    }

    function matchAccounts(
        address makerAddress,
        address takerAddress,
        int256 matchedMakerSizeE9,
        int256 matchedMakerNotionalE18,
        int256 inputNonce
    ) public onlyOwner {
        require(inputNonce == matchNonce + 1, "Incorrect nonce");

        userSizeE9[makerAddress] -= matchedMakerSizeE9;
        userNotionalE18[makerAddress] -= matchedMakerNotionalE18;
        require(
            0 <= availableMarginE18(makerAddress) ||
                makerAddress == settlerAddress,
            "Insufficient margin for maker"
        );

        userSizeE9[takerAddress] += matchedMakerSizeE9;
        userNotionalE18[takerAddress] += matchedMakerNotionalE18;
        require(
            0 <= availableMarginE18(takerAddress) ||
                takerAddress == settlerAddress,
            "Insufficient margin for taker"
        );

        matchNonce++;

        emit PositionUpdated(
            makerAddress,
            userSizeE9[makerAddress],
            userNotionalE18[makerAddress]
        );
        emit PositionUpdated(
            takerAddress,
            userSizeE9[takerAddress],
            userNotionalE18[takerAddress]
        );
        emit AccountsMatched(
            makerAddress,
            takerAddress,
            matchedMakerSizeE9,
            matchedMakerNotionalE18,
            matchNonce
        );
    }

    function settleMarket(address userAddress) internal {
        require(isResolved, "Market is not resolved yet");

        int256 matchedMakerSizeE9 = userSizeE9[userAddress];
        int256 matchedMakerNotionalE18 = 0;
        if (outcome) matchedMakerNotionalE18 = MAX_PRICE_E9 * matchedMakerSizeE9;

        // Call matchAccounts with the updated types and nonce increment
        matchAccounts(
            settlerAddress,
            userAddress,
            matchedMakerSizeE9,
            matchedMakerNotionalE18,
            matchNonce + 1
        );

        emit MarketSettled(userAddress, matchedMakerSizeE9, matchedMakerNotionalE18);
    }

    function resolveOracle() external onlyOwner {
        require(block.timestamp >= endTime, "Market has not ended yet");
        require(!isResolved, "Market already resolved");

        (
            bool _outcome,
            bool resolved,
            bool inDispute
        ) = IOracle(oracleAddress).getOutcome(questionId);

        require(resolved, "Outcome not yet available from Oracle");
        require(!inDispute, "Outcome is currently under dispute");

        uint256 oracleResolutionTime = IOracle(oracleAddress)
            .getResolutionTimestamp(questionId);
        require(
            block.timestamp > oracleResolutionTime + DISPUTE_PERIOD,
            "Dispute period not over"
        );

        outcome = _outcome;
        isResolved = true;
        resolutionTime = block.timestamp;

        emit MarketResolved(outcome);
    }

    function getMarketInfo()
        external
        view
        returns (
            string memory _question,
            uint256 _endTime,
            bool _isResolved,
            bool _outcome
        )
    {
        return (question, endTime, isResolved, outcome);
    }
}
