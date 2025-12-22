// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title DataVerification
 * @dev Blockchain-anchored verification contract for
 *      IIoT Federated Learning lifecycle governance
 */
contract DataVerification {

    // ---------------- EXISTING STATE ----------------
    mapping(bytes32 => bool) public whitelist;
    mapping(bytes32 => bool) public verifiedDataHashes;
    mapping(bytes32 => bool) public verifiedModelHashes;

    // ---------------- NEW STATE (NOVEL ADDITION) ----------------
    // Round ID => Merkle Root of event chain
    mapping(uint256 => bytes32) public roundMerkleRoots;

    // ---------------- EVENTS ----------------
    event DataHashWhitelisted(bytes32 indexed dataHash);
    event DataHashVerified(bytes32 indexed dataHash);
    event ModelHashVerified(bytes32 indexed modelHash);

    // 🔒 NEW: lifecycle anchoring
    event RoundMerkleRootRecorded(uint256 indexed round, bytes32 merkleRoot);

    // ---------------- DATA HASH LOGIC ----------------
    function addToWhitelist(bytes32 hash) public {
        require(!whitelist[hash], "Already whitelisted");
        whitelist[hash] = true;
        emit DataHashWhitelisted(hash);
    }

    function verifyDataHash(bytes32 dataHash) public view returns (bool) {
        return whitelist[dataHash];
    }

    function markDataHashVerified(bytes32 dataHash) public returns (bool) {
        require(whitelist[dataHash], "Not whitelisted");
        verifiedDataHashes[dataHash] = true;
        emit DataHashVerified(dataHash);
        return true;
    }

    // ---------------- MODEL HASH LOGIC ----------------
    function submitModelHash(bytes32 modelHash) public returns (bool) {
        verifiedModelHashes[modelHash] = true;
        emit ModelHashVerified(modelHash);
        return true;
    }

    function verifyModelHash(bytes32 modelHash) public view returns (bool) {
        return verifiedModelHashes[modelHash];
    }

    // ---------------- 🔥 NOVEL FUNCTION ----------------
    /**
     * @notice Records the Merkle root representing the
     *         event-level lifecycle of a federated learning round
     * @param round Federated learning round ID
     * @param root Merkle root of chained event hashes
     */
    function recordRoundMerkleRoot(uint256 round, bytes32 root) public {
        require(roundMerkleRoots[round] == bytes32(0), "Round already anchored");
        roundMerkleRoots[round] = root;
        emit RoundMerkleRootRecorded(round, root);
    }

    /**
     * @notice Verifies if a round has been anchored on-chain
     */
    function verifyRoundMerkleRoot(uint256 round, bytes32 root) public view returns (bool) {
        return roundMerkleRoots[round] == root;
    }
}
