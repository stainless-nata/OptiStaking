// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.5.16;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20Detailed.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

// Inheritance
import "./interfaces/IStakingRewards.sol";
import "./RewardsDistributionRecipient.sol";
import "./Pausable.sol";

// https://docs.synthetix.io/contracts/source/contracts/stakingrewards
contract StakingRewardsClonable is
    IStakingRewards,
    RewardsDistributionRecipient,
    ReentrancyGuard,
    Pausable
{
    using SafeMath for uint256;
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */

    IERC20 public rewardsToken;
    IERC20 public stakingToken;
    uint256 public periodFinish = 0;
    uint256 public rewardRate = 0;
    uint256 public rewardsDuration;
    uint256 public lastUpdateTime;
    uint256 public rewardPerTokenStored;
    address public zapContract;
    bool public isRetired;

    mapping(address => uint256) public userRewardPerTokenPaid;
    mapping(address => uint256) public rewards;

    uint256 private _totalSupply;
    mapping(address => uint256) private _balances;

    /// @notice Will only be true on the original deployed contract and not on clones; we don't want to clone a clone.
    bool public isOriginal = true;

    /* ========== CONSTRUCTOR ========== */

    constructor(
        address _owner,
        address _rewardsDistribution,
        address _rewardsToken,
        address _stakingToken,
        address _zapContract
    ) public Owned(_owner) {
        _initializePool(
            _rewardsDistribution,
            _rewardsToken,
            _stakingToken,
            _zapContract
        );
    }

    /* ========== CLONING ========== */

    event Cloned(address indexed clone);

    /// @notice Use this to clone an exact copy of this staking pool.
    /// @dev Note that owner will have to call acceptOwnership() to assume ownership of the new staking pool.
    /// @param _owner Owner of the new staking contract.
    /// @param _rewardsDistribution Only this address can call notifyRewardAmount, to add more rewards.
    /// @param _rewardsToken Address of our rewards token.
    /// @param _stakingToken Address of our staking token.
    /// @param _zapContract Address of our zap contract.
    function cloneStakingPool(
        address _owner,
        address _rewardsDistribution,
        address _rewardsToken,
        address _stakingToken,
        address _zapContract
    ) external returns (address newStakingPool) {
        // don't clone a clone
        if (!isOriginal) {
            revert();
        }

        // Copied from https://github.com/optionality/clone-factory/blob/master/contracts/CloneFactory.sol
        bytes20 addressBytes = bytes20(address(this));
        assembly {
            // EIP-1167 bytecode
            let clone_code := mload(0x40)
            mstore(
                clone_code,
                0x3d602d80600a3d3981f3363d3d373d3d3d363d73000000000000000000000000
            )
            mstore(add(clone_code, 0x14), addressBytes)
            mstore(
                add(clone_code, 0x28),
                0x5af43d82803e903d91602b57fd5bf30000000000000000000000000000000000
            )
            newStakingPool := create(0, clone_code, 0x37)
        }

        StakingRewardsClonable(newStakingPool).initialize(
            _rewardsDistribution,
            _rewardsToken,
            _stakingToken,
            _zapContract
        );

        emit Cloned(newStakingPool);
    }

    /// @notice Initialize the staking pool.
    /// @dev This should only be called by the clone function above.
    /// @param _rewardsDistribution Only this address can call notifyRewardAmount, to add more rewards.
    /// @param _rewardsToken Address of our rewards token.
    /// @param _stakingToken Address of our staking token.
    /// @param _zapContract Address of our zap contract.
    function initialize(
        address _rewardsDistribution,
        address _rewardsToken,
        address _stakingToken,
        address _zapContract
    ) public {
        _initializePool(
            _rewardsDistribution,
            _rewardsToken,
            _stakingToken,
            _zapContract
        );
    }

    // this is called by our original staking pool, as well as any clones via the above function
    function _initializePool(
        address _rewardsDistribution,
        address _rewardsToken,
        address _stakingToken,
        address _zapContract
    ) internal {
        // make sure that we haven't initialized this before
        if (address(rewardsToken) != address(0)) {
            revert(); // already initialized.
        }

        // set up our state vars
        rewardsToken = IERC20(_rewardsToken);
        stakingToken = IERC20(_stakingToken);
        rewardsDistribution = _rewardsDistribution;
        zapContract = _zapContract;

        // default duration to 7 days
        rewardsDuration = 7 days;
    }

    /* ========== VIEWS ========== */

    function totalSupply() external view returns (uint256) {
        return _totalSupply;
    }

    function balanceOf(address account) external view returns (uint256) {
        return _balances[account];
    }

    function lastTimeRewardApplicable() public view returns (uint256) {
        return block.timestamp < periodFinish ? block.timestamp : periodFinish;
    }

    function rewardPerToken() public view returns (uint256) {
        if (_totalSupply == 0) {
            return rewardPerTokenStored;
        }

        if (isRetired) {
            return 0;
        }

        return
            rewardPerTokenStored.add(
                lastTimeRewardApplicable()
                    .sub(lastUpdateTime)
                    .mul(rewardRate)
                    .mul(1e18)
                    .div(_totalSupply)
            );
    }

    function earned(address account) public view returns (uint256) {
        if (isRetired) {
            return 0;
        }

        return
            _balances[account]
                .mul(rewardPerToken().sub(userRewardPerTokenPaid[account]))
                .div(1e18)
                .add(rewards[account]);
    }

    function getRewardForDuration() external view returns (uint256) {
        return rewardRate.mul(rewardsDuration);
    }

    /* ========== MUTATIVE FUNCTIONS ========== */

    /// @notice Deposit vault tokens to the staking pool.
    /// @dev Can't stake zero.
    /// @param amount Amount of vault tokens to deposit.
    function stake(uint256 amount)
        external
        nonReentrant
        notPaused
        updateReward(msg.sender)
    {
        require(amount > 0, "Cannot stake 0");
        require(!isRetired, "Staking pool is retired");
        _totalSupply = _totalSupply.add(amount);
        _balances[msg.sender] = _balances[msg.sender].add(amount);
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        emit Staked(msg.sender, amount);
    }

    /// @notice Deposit vault tokens for specified recipient.
    /// @dev Can't stake zero, can only be used by zap contract.
    /// @param recipient Address of user these vault tokens are being staked for.
    /// @param amount Amount of vault token to deposit.
    function stakeFor(address recipient, uint256 amount)
        external
        nonReentrant
        notPaused
        updateReward(recipient)
    {
        require(msg.sender == zapContract, "Only zap contract");
        require(amount > 0, "Cannot stake 0");
        require(!isRetired, "Staking pool is retired");
        _totalSupply = _totalSupply.add(amount);
        _balances[recipient] = _balances[recipient].add(amount);
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        emit StakedFor(recipient, amount);
    }

    /// @notice Withdraw vault tokens from the staking pool.
    /// @dev Can't withdraw zero. If trying to claim, call getReward() instead.
    /// @param amount Amount of vault tokens to withdraw.
    function withdraw(uint256 amount)
        public
        nonReentrant
        updateReward(msg.sender)
    {
        require(amount > 0, "Cannot withdraw 0");
        _totalSupply = _totalSupply.sub(amount);
        _balances[msg.sender] = _balances[msg.sender].sub(amount);
        stakingToken.safeTransfer(msg.sender, amount);
        emit Withdrawn(msg.sender, amount);
    }

    /// @notice Claim any earned reward tokens.
    /// @dev Can claim rewards even if no tokens still staked.
    function getReward() public nonReentrant updateReward(msg.sender) {
        uint256 reward = rewards[msg.sender];
        if (reward > 0) {
            rewards[msg.sender] = 0;
            rewardsToken.safeTransfer(msg.sender, reward);
            emit RewardPaid(msg.sender, reward);
        }
    }

    /// @notice Unstake all of the sender's tokens and claim any outstanding rewards.
    function exit() external {
        withdraw(_balances[msg.sender]);
        getReward();
    }

    /* ========== RESTRICTED FUNCTIONS ========== */

    /// @notice Notify staking contract that it has more reward to account for.
    /// @dev Reward tokens must be sent to contract before notifying. May only be called
    ///  by rewards distribution role.
    /// @param reward Amount of reward tokens to add.
    function notifyRewardAmount(uint256 reward)
        external
        onlyRewardsDistribution
        updateReward(address(0))
    {
        if (block.timestamp >= periodFinish) {
            rewardRate = reward.div(rewardsDuration);
        } else {
            uint256 remaining = periodFinish.sub(block.timestamp);
            uint256 leftover = remaining.mul(rewardRate);
            rewardRate = reward.add(leftover).div(rewardsDuration);
        }

        // Ensure the provided reward amount is not more than the balance in the contract.
        // This keeps the reward rate in the right range, preventing overflows due to
        // very high values of rewardRate in the earned and rewardsPerToken functions;
        // Reward + leftover must be less than 2^256 / 10^18 to avoid overflow.
        uint256 balance = rewardsToken.balanceOf(address(this));
        require(
            rewardRate <= balance.div(rewardsDuration),
            "Provided reward too high"
        );

        lastUpdateTime = block.timestamp;
        periodFinish = block.timestamp.add(rewardsDuration);
        emit RewardAdded(reward);
    }

    /// @notice Sweep out tokens accidentally sent here.
    /// @dev May only be called by owner.
    /// @param tokenAddress Address of token to sweep.
    /// @param tokenAmount Amount of tokens to sweep.
    function recoverERC20(address tokenAddress, uint256 tokenAmount)
        external
        onlyOwner
    {
        require(
            tokenAddress != address(stakingToken),
            "Cannot withdraw the staking token"
        );

        // can only recover rewardsToken 90 days after end
        if (tokenAddress == address(rewardsToken)) {
            require(
                block.timestamp > periodFinish + 90 days,
                "wait 90 days to sweep leftover rewards"
            );

            // if we do this, automatically sweep all rewardsToken
            tokenAmount = rewardsToken.balanceOf(address(this));

            // retire this staking contract, this wipes all rewards but still allows all users to withdraw
            isRetired = true;
        }

        IERC20(tokenAddress).safeTransfer(owner, tokenAmount);
        emit Recovered(tokenAddress, tokenAmount);
    }

    function setRewardsDuration(uint256 _rewardsDuration) external onlyOwner {
        require(
            block.timestamp > periodFinish,
            "Previous rewards period must be complete before changing the duration for the new period"
        );
        rewardsDuration = _rewardsDuration;
        emit RewardsDurationUpdated(rewardsDuration);
    }

    function setZapContract(address _zapContract) external onlyOwner {
        require(_zapContract != address(0), "no zero address");
        zapContract = _zapContract;
        emit ZapContractUpdated(_zapContract);
    }

    /* ========== MODIFIERS ========== */

    modifier updateReward(address account) {
        rewardPerTokenStored = rewardPerToken();
        lastUpdateTime = lastTimeRewardApplicable();
        if (account != address(0)) {
            rewards[account] = earned(account);
            userRewardPerTokenPaid[account] = rewardPerTokenStored;
        }
        _;
    }

    /* ========== EVENTS ========== */

    event RewardAdded(uint256 reward);
    event Staked(address indexed user, uint256 amount);
    event StakedFor(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardPaid(address indexed user, uint256 reward);
    event RewardsDurationUpdated(uint256 newDuration);
    event ZapContractUpdated(address _zapContract);
    event Recovered(address token, uint256 amount);
}
