// SPDX-License-Identifier: MIT
pragma solidity ^0.8.22;

import "@openzeppelin/contracts/access/Ownable.sol";

contract Oracle is Ownable {
    uint256 public constant DISPUTE_PERIOD = 3 minutes;
    uint256 public constant DISPUTE_STAKE = 30 ether;

    mapping(bytes32 => bool) public outcomes;
    mapping(bytes32 => bool) public isResolved;
    mapping(bytes32 => uint256) public resolutionTimestamps;
    mapping(bytes32 => address) public disputeInitiator;

    event OutcomeReported(bytes32 indexed questionId, bool outcome);
    event OutcomeDisputed(bytes32 indexed questionId, address disputer);
    event DisputeResolved(bytes32 indexed questionId, bool originalOutcomeStood);

    constructor() Ownable(msg.sender) {}

    function reportOutcome(bytes32 questionId, bool outcome) external onlyOwner {
        outcomes[questionId] = outcome;
        resolutionTimestamps[questionId] = block.timestamp;
        isResolved[questionId] = true;
        emit OutcomeReported(questionId, outcome);
    }

    function disputeOutcome(bytes32 questionId) external payable {
        require(resolutionTimestamps[questionId] != 0, "Outcome not reported");
        require(block.timestamp <= resolutionTimestamps[questionId] + DISPUTE_PERIOD, "Dispute period over");
        require(msg.value == DISPUTE_STAKE, "Incorrect dispute stake");

        disputeInitiator[questionId] = msg.sender;
        isResolved[questionId] = false;
        
        emit OutcomeDisputed(questionId, msg.sender);
    }

    function resolveDispute(bytes32 questionId, bool originalOutcomeStood) external onlyOwner {
        require(disputeInitiator[questionId] != address(0), "No active dispute");
        
        address payable recipient = originalOutcomeStood ? payable(owner()) : payable(disputeInitiator[questionId]);
        (bool sent, ) = recipient.call{value: DISPUTE_STAKE}("");
        require(sent, "Failed to send Ether");

        if (!originalOutcomeStood) {
            // Flip the outcome if the original outcome did not stand
            outcomes[questionId] = !outcomes[questionId];
        }
        
        isResolved[questionId] = true;
        disputeInitiator[questionId] = address(0);
        emit DisputeResolved(questionId, originalOutcomeStood);
    }

    function getOutcome(bytes32 questionId) external view returns (uint256, bool, bool, bool) {
        return (outcomes[questionId], isResolved[questionId], disputeInitiator[questionId] != address(0));
    }

    function getResolutionTimestamp(bytes32 questionId) external view returns (uint256){
        return resolutionTimestamps[questionId];
    }

    // Function to receive Ether. msg.data must be empty
    receive() external payable {}

    // Fallback function is called when msg.data is not empty
    fallback() external payable {}
}