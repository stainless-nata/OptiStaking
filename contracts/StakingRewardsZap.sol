// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.8.15;

import "@openzeppelin_new/contracts/access/Ownable.sol";
import "@openzeppelin_new/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin_new/contracts/token/ERC20/utils/SafeERC20.sol";

interface IVault is IERC20 {
    function token() external view returns (address);

    function deposit() external;
}

interface IStakingRewards {
    function stakeFor(address recipient, uint256 amount) external;
}

interface IRegistry {
    function stakingPool(address vault) external view returns (address);
}

contract StakingRewardsZap is Ownable {
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */

    /// @notice Address of our staking pool registry.
    address public stakingPoolRegistry;

    /* ========== EVENTS ========== */

    event ZapIn(
        address indexed user,
        address indexed targetVault,
        uint256 amount
    );

    event UpdatedPoolRegistry(address registry);
    event Recovered(address token, uint256 amount);

    /* ========== CONSTRUCTOR ========== */

    constructor(address _stakingPoolRegistry) {
        stakingPoolRegistry = _stakingPoolRegistry;
    }

    /* ========== MUTATIVE FUNCTIONS ========== */

    function zapIn(address _targetVault, uint256 _underlyingAmount)
        external
        returns (uint256)
    {
        // get our underlying token
        IVault targetVault = IVault(_targetVault);
        IERC20 underlying = IERC20(targetVault.token());

        // transfer to zap and deposit underlying to vault, but first check our approvals
        _checkAllowance(_targetVault, address(underlying), _underlyingAmount);
        underlying.transferFrom(msg.sender, address(this), _underlyingAmount);
        targetVault.deposit();

        // read staking contract from registry, then deposit to that staking contract
        uint256 toStake = targetVault.balanceOf(address(this));

        // get our staking pool from our registry for this vault token
        IRegistry poolRegistry = IRegistry(stakingPoolRegistry);

        // check what our address is, make sure it's not zero
        address _vaultStakingPool = poolRegistry.stakingPool(_targetVault);
        require(_vaultStakingPool != address(0), "staking pool doesn't exist");
        IStakingRewards vaultStakingPool = IStakingRewards(_vaultStakingPool);

        // make sure we have approved the staking pool, as they can be added/updated at any time
        _checkAllowance(_vaultStakingPool, _targetVault, toStake);

        // stake for our user, return the amount we staked
        vaultStakingPool.stakeFor(msg.sender, toStake);
        emit ZapIn(msg.sender, address(targetVault), toStake);
        return toStake;
    }

    function _checkAllowance(
        address _contract,
        address _token,
        uint256 _amount
    ) internal {
        if (IERC20(_token).allowance(address(this), _contract) < _amount) {
            IERC20(_token).safeApprove(_contract, 0);
            IERC20(_token).safeApprove(_contract, type(uint256).max);
        }
    }

    /// @notice Use this in case someone accidentally sends tokens here.
    function recoverERC20(address tokenAddress, uint256 tokenAmount)
        external
        onlyOwner
    {
        IERC20(tokenAddress).safeTransfer(owner(), tokenAmount);
        emit Recovered(tokenAddress, tokenAmount);
    }

    /* ========== SETTERS ========== */

    /**
    @notice Set the registry for pulling our staking pools.
    @dev Throws if caller is not owner.
    @param _stakingPoolRegistry The address to use as pool registry.
     */
    function setPoolRegistry(address _stakingPoolRegistry) external onlyOwner {
        stakingPoolRegistry = _stakingPoolRegistry;
        emit UpdatedPoolRegistry(_stakingPoolRegistry);
    }
}
