// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

interface IOracle {
    function getOutcome(
        bytes32 questionId
    ) external view returns (int256, bool, bool, bool);

    function getResolutionTimestamp(
        bytes32 questionId
    ) external view returns (uint256);
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

    int256 public MAX_PRICE;

    int256 public nonce;

    address public settlerAddress;

    mapping(address => bool) public hasClaimed;

    mapping(address => int256) public userBalance;
    mapping(address => int256) public userSize;
    mapping(address => int256) public userNotional;

    event MarketCreated(
        string question,
        uint256 endTime,
        address oracleAddress,
        int256 maxPrice
    );
    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);
    event PositionUpdated(
        address indexed user,
        int256 newSize,
        int256 newNotional
    );
    event MarketSettled(
        address indexed user,
        int256 settledSize,
        int256 settledNotional
    );
    event MarketResolved(bool outcome);
    event AccountsMatched(
        address indexed maker,
        address indexed taker,
        int256 size,
        int256 notional,
        int256 newNonce
    );

    event Debug(int256 uintNumber, int256 intNumber);

    constructor(
        string memory _question,
        uint256 _endTime,
        address _oracleAddress,
        int256 _MAX_PRICE
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
        userBalance[msg.sender] += int256(msg.value); // Cast msg.value to int256
        emit Deposit(msg.sender, msg.value);
    }

    function withdraw(uint256 amount) external nonReentrant {
        if (isResolved && userSize[msg.sender] != 0) settleMarket(msg.sender);

        userBalance[msg.sender] -= int256(amount);
        require(0 <= availableMargin(msg.sender), "Insufficient funds");

        (bool success, ) = payable(msg.sender).call{value: amount}("");
        require(success, "ETH transfer failed");

        emit Withdrawal(msg.sender, amount);
    }

    function worstPNL(address userAddress) public view returns (int256 pnl) {
        int256 worstExitNotional = 0;
        if (userSize[userAddress] < 0)
            worstExitNotional = MAX_PRICE * userSize[userAddress];

        return worstExitNotional - userNotional[userAddress];
    }

    function availableMargin(
        address userAddress
    ) public view returns (int256 margin) {
        return userBalance[userAddress] + worstPNL(userAddress);
    }

    function matchAccounts(
        address makerAddress,
        address takerAddress,
        int256 matchedMakerSize,
        int256 matchedMakerNotional,
        int256 inputNonce
    ) public onlyOwner {
        require(inputNonce == nonce + 1, "Incorrect nonce");

        userSize[makerAddress] -= matchedMakerSize;
        userNotional[makerAddress] -= matchedMakerNotional;
        require(
            0 <= availableMargin(makerAddress) ||
                makerAddress == settlerAddress,
            "Insufficient margin for maker"
        );

        userSize[takerAddress] += matchedMakerSize;
        userNotional[takerAddress] += matchedMakerNotional;
        require(
            0 <= availableMargin(takerAddress) ||
                takerAddress == settlerAddress,
            "Insufficient margin for taker"
        );

        nonce++;

        emit PositionUpdated(
            makerAddress,
            userSize[makerAddress],
            userNotional[makerAddress]
        );
        emit PositionUpdated(
            takerAddress,
            userSize[takerAddress],
            userNotional[takerAddress]
        );
        emit AccountsMatched(
            makerAddress,
            takerAddress,
            matchedMakerSize,
            matchedMakerNotional,
            nonce
        );
    }

    function settleMarket(address userAddress) internal {
        require(isResolved, "Market is not resolved yet");

        int256 matchedMakerSize = userSize[userAddress];
        int256 matchedMakerNotional = 0;
        if (outcome) matchedMakerNotional = MAX_PRICE * matchedMakerSize;

        // Call matchAccounts with the updated types and nonce increment
        matchAccounts(
            settlerAddress,
            userAddress,
            matchedMakerSize,
            matchedMakerNotional,
            nonce + 1
        );

        emit MarketSettled(userAddress, matchedMakerSize, matchedMakerNotional);
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
