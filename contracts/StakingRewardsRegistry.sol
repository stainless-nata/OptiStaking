// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

import "@openzeppelin/contracts/access/Ownable.sol";

interface IStakingRewards {
    function stakingToken() external view returns (address);

    function owner() external view returns (address);
}

contract StakingRewardsRegistry is Ownable {
    /* ========== STATE VARIABLES ========== */

    /// @notice If a stakingPool exists for a given token, it will be shown here.
    /// @dev Only stakingPools added to this registry will be shown.
    mapping(address => address) public stakingPool;

    /// @notice Tokens that this registry has added stakingPools for.
    address[] public tokens;

    /// @notice Check if an stakingPool exists for a given vault token.
    mapping(address => bool) public isRegistered;

    /// @notice Check if an address is allowed to own stakingPools from this registry.
    mapping(address => bool) public approvedPoolOwner;

    /// @notice Check if a given stakingPool is known to this registry.
    mapping(address => bool) public isStakingPoolEndorsed;

    /// @notice Check if an address can add pools to this registry.
    mapping(address => bool) public poolEndorsers;

    /* ========== EVENTS ========== */

    event StakingPoolAdded(address indexed token, address indexed stakingPool);

    event ApprovedPoolOwnerUpdated(address governance, bool approved);
    event ApprovedPoolEndorser(address account, bool canEndorse);

    /* ========== VIEWS ========== */

    /// @notice The number of tokens with staking pools added to this registry.
    function numTokens() external view returns (uint256) {
        return tokens.length;
    }

    /* ========== CORE FUNCTIONS ========== */

    /**
    @notice
        Add a new staking pool to our registry, for new or existing tokens.
    @dev
        Throws if governance isn't set properly.
        Throws if sender isn't allowed to endorse.
        Throws if replacement is handled improperly.
        Emits a StakingPoolAdded event.
    @param _token The token that may be deposited into the new staking pool.
    @param _guardian The address of the new staking pool.
    @param _replaceExistingPool If we are replacing an existing staking pool, set this to true.
     */
    function addStakingPool(
        address _token,
        address _stakingPool,
        bool _replaceExistingPool
    ) public {
        // don't let just anyone add to our registry
        require(poolEndorsers[msg.sender], "unauthorized");

        // load up the staking pool contract
        IStakingRewards stakingRewards = IStakingRewards(_stakingPool);

        // check that gov is correct on the staking contract
        address poolGov = stakingRewards.owner();
        require(approvedPoolOwner[poolGov], "not allowed pool owner");

        // make sure we didn't mess up our token/staking pool match
        require(
            stakingRewards.stakingToken() == _token,
            "staking token doesn't match"
        );

        // Make sure we're only using the latest stakingPool in our registry
        if (_replaceExistingPool) {
            require(
                isRegistered[_token] == true,
                "token isn't registered, can't replace"
            );
            address oldPool = stakingPools[_token];
            isStakingPoolEndorsed[oldPool] = false;
            stakingPools[_token] = _stakingPool;
        } else {
            require(
                isRegistered[_token] == false,
                "replace instead, pool already exists"
            );
            stakingPools[_token].push(_stakingPool);
            isRegistered[_token] = true;
            tokens.push(_token);
        }

        isStakingPoolEndorsed[_stakingPool] = true;
        emit StakingPoolAdded(_token, _stakingPool);
    }

    /* ========== SETTERS ========== */

    /**
    @notice Set the ability of an address to endorse staking pools.
    @dev Throws if caller is not owner.
    @param _addr The address to approve or deny access.
    @param _approved Allowed to endorse
     */
    function setPoolEndorsers(address _addr, bool _approved)
        external
        onlyOwner
    {
        poolEndorsers[_addr] = _approved;
        emit ApprovedPoolEndorser(_addr, _approved);
    }

    /**
    @notice Set the staking pool owners
    @dev Throws if caller is not owner.
    @param _addr The address to approve or deny access.
    @param _approved Allowed to own staking pools
     */
    function setApprovedPoolOwner(address _addr, bool _approved)
        external
        onlyOwner
    {
        approvedPoolOwner[_addr] = _approved;
        emit ApprovedPoolOwnerUpdated(_addr, _approved);
    }
}
