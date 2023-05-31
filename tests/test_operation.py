import brownie
from brownie import ZERO_ADDRESS, chain, interface
import pytest

# this test asserts that a newly deployed zap with a newly deployed registry works as expected
def test_normal_deposit(
    gov,
    yvdai,
    yvdai_amount,
    yvdai_whale,
    yvusdc,
    yvusdc_amount,
    yvusdc_whale,
    yvop,
    yvop_whale,
    registry,
    zap,
    yvdai_pool,
    yvusdc_pool,
    dai,
):
    # Approve and deposit to the staking contract
    yvdai_starting = yvdai.balanceOf(yvdai_whale)
    yvdai.approve(yvdai_pool, 2**256 - 1, {"from": yvdai_whale})
    yvdai_pool.stake(yvdai_amount, {"from": yvdai_whale})
    assert yvdai_pool.balanceOf(yvdai_whale) == yvdai_amount

    # can't stake zero
    with brownie.reverts("Cannot stake 0"):
        yvdai_pool.stake(0, {"from": yvdai_whale})

    # whale sends directly to pool, gov notifies rewards
    yvop.transfer(yvdai_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    yvdai_pool.notifyRewardAmount(100e18, {"from": gov})

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, get reward
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned > 0
    yvdai_pool.getReward({"from": yvdai_whale})
    assert yvop.balanceOf(yvdai_whale) >= earned
    assert yvdai_pool.getRewardForDuration({"from": yvdai_whale}) > 0

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # can't withdraw zero
    with brownie.reverts("Cannot withdraw 0"):
        yvdai_pool.withdraw(0, {"from": yvdai_whale})

    # exit, check that we have the same principal and earned more rewards
    yvdai_pool.exit({"from": yvdai_whale})
    assert yvdai_starting == yvdai.balanceOf(yvdai_whale)
    assert yvop.balanceOf(yvdai_whale) > earned

    # check our setters
    with brownie.reverts():
        yvdai_pool.setRewardsDuration(100e18, {"from": gov})
    with brownie.reverts():
        yvdai_pool.setZapContract(ZERO_ADDRESS, {"from": gov})
    yvdai_pool.setZapContract(zap, {"from": gov})

    # sleep to get past our rewards window
    chain.sleep(86400 * 6)
    yvdai_pool.setRewardsDuration(86400 * 14, {"from": gov})
    assert dai.balanceOf(zap) == 0


def test_insanity(
    gov,
    yvdai,
    yvdai_amount,
    yvdai_whale,
    yvusdc,
    yvusdc_amount,
    yvusdc_whale,
    yvop,
    yvop_whale,
    registry,
    zap,
    yvdai_pool,
    yvusdc_pool,
    dai,
    dai_whale,
    dai_amount,
):
    # Approve and deposit to the staking contract
    yvdai_starting = yvdai.balanceOf(yvdai_whale)
    yvdai.approve(yvdai_pool, 2**256 - 1, {"from": yvdai_whale})
    yvdai_pool.stake(yvdai_amount, {"from": yvdai_whale})
    assert yvdai_pool.balanceOf(yvdai_whale) == yvdai_amount

    # whale sends directly to pool, gov notifies rewards
    yvop.transfer(yvdai_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    yvdai_pool.notifyRewardAmount(100e18, {"from": gov})

    # make sure we start with nothing
    assert yvop.balanceOf(yvdai_whale) == 0

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, get reward
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned > 0
    assert yvdai_pool.userRewardPerTokenPaid(yvdai_whale) == 0

    # rewardPerToken() was last calculated here
    print("\nReward per token before getReward call:", yvdai_pool.rewardPerToken())
    print("rewardPerTokenStored:", yvdai_pool.rewardPerTokenStored())
    print("userRewardPerTokenPaid:", yvdai_pool.userRewardPerTokenPaid(yvdai_whale))
    print("lastTimeRewardApplicable:", yvdai_pool.lastTimeRewardApplicable())
    print("lastUpdateTime:", yvdai_pool.lastUpdateTime())
    print("rewardRate:", yvdai_pool.rewardRate())
    print("_totalSupply:", yvdai_pool.totalSupply())
    print("Earned:", yvdai_pool.earned(yvdai_whale))
    print("rewards:", yvdai_pool.rewards(yvdai_whale))

    yvdai_pool.getReward({"from": yvdai_whale})

    print("\nReward per token after getReward:", yvdai_pool.rewardPerToken())
    print("rewardPerTokenStored:", yvdai_pool.rewardPerTokenStored())
    print("userRewardPerTokenPaid:", yvdai_pool.userRewardPerTokenPaid(yvdai_whale))
    print("lastTimeRewardApplicable:", yvdai_pool.lastTimeRewardApplicable())
    print("lastUpdateTime:", yvdai_pool.lastUpdateTime())
    print("rewardRate:", yvdai_pool.rewardRate())
    print("_totalSupply:", yvdai_pool.totalSupply())
    print("Earned:", yvdai_pool.earned(yvdai_whale))
    print("rewards:", yvdai_pool.rewards(yvdai_whale))

    claimed = yvop.balanceOf(yvdai_whale)
    print("Claimed:", claimed)
    staking_token = interface.IERC20(yvdai_pool.stakingToken())
    reward_per_token = yvdai_pool.userRewardPerTokenPaid(yvdai_whale)
    tokens = int(yvdai_pool.balanceOf(yvdai_whale) / (10 ** staking_token.decimals()))
    answer = reward_per_token * tokens
    assert answer == claimed

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    print("\nReward per token after sleeping for a day:", yvdai_pool.rewardPerToken())
    print("rewardPerTokenStored:", yvdai_pool.rewardPerTokenStored())
    print("userRewardPerTokenPaid:", yvdai_pool.userRewardPerTokenPaid(yvdai_whale))
    print("lastTimeRewardApplicable:", yvdai_pool.lastTimeRewardApplicable())
    print("lastUpdateTime:", yvdai_pool.lastUpdateTime())
    print("rewardRate:", yvdai_pool.rewardRate())
    print("_totalSupply:", yvdai_pool.totalSupply())
    print("Earned:", yvdai_pool.earned(yvdai_whale))
    print("rewards:", yvdai_pool.rewards(yvdai_whale))

    yvdai_pool.getReward({"from": yvdai_whale})

    print("\nReward per token after getReward:", yvdai_pool.rewardPerToken())
    print("rewardPerTokenStored:", yvdai_pool.rewardPerTokenStored())
    print("userRewardPerTokenPaid:", yvdai_pool.userRewardPerTokenPaid(yvdai_whale))
    print("lastTimeRewardApplicable:", yvdai_pool.lastTimeRewardApplicable())
    print("lastUpdateTime:", yvdai_pool.lastUpdateTime())
    print("rewardRate:", yvdai_pool.rewardRate())
    print("_totalSupply:", yvdai_pool.totalSupply())
    print("Earned:", yvdai_pool.earned(yvdai_whale))
    print("rewards:", yvdai_pool.rewards(yvdai_whale))

    # this hasn't been reset to zero yet
    claimed = yvop.balanceOf(yvdai_whale)
    print("Claimed:", claimed)
    staking_token = interface.IERC20(yvdai_pool.stakingToken())
    reward_per_token = yvdai_pool.userRewardPerTokenPaid(yvdai_whale)
    tokens = int(yvdai_pool.balanceOf(yvdai_whale) / (10 ** staking_token.decimals()))
    answer = reward_per_token * tokens
    assert answer == claimed


def test_sweep_rewards(
    gov,
    yvdai,
    yvdai_amount,
    yvdai_whale,
    yvusdc,
    yvusdc_amount,
    yvusdc_whale,
    yvop,
    yvop_whale,
    registry,
    zap,
    yvdai_pool,
    yvusdc_pool,
    dai,
    dai_whale,
    dai_amount,
):
    # Approve and deposit to the staking contract
    yvdai_starting = yvdai.balanceOf(yvdai_whale)
    yvdai.approve(yvdai_pool, 2**256 - 1, {"from": yvdai_whale})
    yvdai_pool.stake(yvdai_amount, {"from": yvdai_whale})
    assert yvdai_pool.balanceOf(yvdai_whale) == yvdai_amount

    # whale sends directly to pool, gov notifies rewards
    yvop.transfer(yvdai_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    yvdai_pool.notifyRewardAmount(100e18, {"from": gov})

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, get reward
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned > 0
    yvdai_pool.getReward({"from": yvdai_whale})
    claimed = yvop.balanceOf(yvdai_whale)

    # do >= since we (sometimes?) get extra in the block it takes to harvest
    assert claimed >= earned
    print("Earned:", earned / 1e18, "Claimed:", claimed / 1e18)

    # check that we can't sweep out yvOP or the staking token
    with brownie.reverts():
        yvdai_pool.recoverERC20(yvdai_pool.rewardsToken(), 10e18, {"from": gov})
    with brownie.reverts():
        yvdai_pool.recoverERC20(yvdai_pool.stakingToken(), 10e18, {"from": gov})

    # we can sweep out DAI tho
    dai.transfer(yvdai_pool, 100e18, {"from": dai_whale})
    assert dai.balanceOf(yvdai_pool) > 0
    yvdai_pool.recoverERC20(dai, 100e18, {"from": gov})
    assert dai.balanceOf(yvdai_pool) == 0

    # sleep 91 days so we can sweep out rewards
    chain.sleep(86400 * 100)
    chain.mine(1)
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned > 0
    assert yvop.balanceOf(yvdai_pool) > 0

    # amount doesn't matter since we auto-sweep all rewards token
    yvdai_pool.recoverERC20(yvdai_pool.rewardsToken(), 10e18, {"from": gov})
    assert yvop.balanceOf(yvdai_pool) == 0

    # this hasn't been reset to zero yet. multiply by amount of whole tokens we have
    staking_token = interface.IERC20(yvdai_pool.stakingToken())
    reward_per_token = yvdai_pool.userRewardPerTokenPaid(yvdai_whale)
    tokens = int(yvdai_pool.balanceOf(yvdai_whale) / (10 ** staking_token.decimals()))
    answer = reward_per_token * tokens
    assert answer == claimed

    # check our earned, should be zeroed
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned == 0
    assert yvdai_pool.rewardPerToken() == 0
    assert yvdai_pool.rewards(yvdai_whale) == 0

    # make sure we can get rewards and nothing happens
    before = yvop.balanceOf(yvdai_whale)
    yvdai_pool.getReward({"from": yvdai_whale})
    after = yvop.balanceOf(yvdai_whale)
    assert before == after

    # now this should be zero since we called updateReward when calling getReward
    assert yvdai_pool.userRewardPerTokenPaid(yvdai_whale) == 0

    # make sure our whale can still withdraw
    yvdai_pool.exit({"from": yvdai_whale})
    assert yvdai_starting == yvdai.balanceOf(yvdai_whale)
    assert yvop.balanceOf(yvdai_whale) > 0
    assert yvdai_pool.userRewardPerTokenPaid(yvdai_whale) == 0

    # check that we can't stake or zap in
    with brownie.reverts("Staking pool is retired"):
        yvdai_pool.stake(yvdai_amount, {"from": yvdai_whale})
    registry.addStakingPool(yvdai_pool, yvdai, False, {"from": gov})
    dai.approve(zap, 2**256 - 1, {"from": dai_whale})
    with brownie.reverts("Staking pool is retired"):
        zap.zapIn(yvdai, dai_amount, {"from": dai_whale})


def test_extend_rewards(
    gov,
    yvdai,
    yvdai_amount,
    yvdai_whale,
    yvusdc,
    yvusdc_amount,
    yvusdc_whale,
    yvop,
    yvop_whale,
    registry,
    zap,
    yvdai_pool,
    yvusdc_pool,
):
    # Approve and deposit to the staking contract
    yvdai_starting = yvdai.balanceOf(yvdai_whale)
    yvdai.approve(yvdai_pool, 2**256 - 1, {"from": yvdai_whale})
    yvdai_pool.stake(yvdai_amount, {"from": yvdai_whale})
    assert yvdai_pool.balanceOf(yvdai_whale) == yvdai_amount

    # whale sends directly to pool, gov notifies rewards
    yvop.transfer(yvdai_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    yvdai_pool.notifyRewardAmount(100e18, {"from": gov})

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, get reward
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned > 0
    yvdai_pool.getReward({"from": yvdai_whale})
    claimed = yvop.balanceOf(yvdai_whale)
    assert yvop.balanceOf(yvdai_whale) >= earned
    assert yvdai_pool.earned(yvdai_whale) == 0

    # do >= since we (sometimes?) get extra in the block it takes to harvest
    assert claimed >= earned
    print("Earned:", earned / 1e18, "Claimed:", claimed / 1e18)

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings again
    earned = yvdai_pool.earned(yvdai_whale)
    assert earned > 0
    print("Earned:", earned / 1e18)

    # add more rewards
    yvop.transfer(yvdai_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    yvdai_pool.notifyRewardAmount(100e18, {"from": gov})

    # can't add too much
    with brownie.reverts("Provided reward too high"):
        yvdai_pool.notifyRewardAmount(10_000e18, {"from": gov})

    # check claimable earnings, make sure we have at least as much as before
    new_earned = yvdai_pool.earned(yvdai_whale)
    assert new_earned >= earned
    print("New Earned after notify:", new_earned / 1e18)

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, make sure we have more than before
    new_earned = yvdai_pool.earned(yvdai_whale)
    before_balance = yvop.balanceOf(yvdai_whale)
    yvdai_pool.getReward({"from": yvdai_whale})
    assert yvop.balanceOf(yvdai_whale) - before_balance >= earned
    print("New Earned after sleep:", new_earned / 1e18)

    # exit, check that we have the same principal and earned more rewards
    yvdai_pool.exit({"from": yvdai_whale})
    assert yvdai_starting == yvdai.balanceOf(yvdai_whale)
    assert yvop.balanceOf(yvdai_whale) > earned


def test_zap(
    gov,
    yvdai,
    yvdai_amount,
    yvdai_whale,
    dai,
    dai_amount,
    dai_whale,
    yvusdc,
    yvusdc_amount,
    yvusdc_whale,
    yvop,
    yvop_whale,
    registry,
    zap,
    yvdai_pool,
    yvusdc_pool,
    RELATIVE_APPROX,
):
    # Approve and zap into to the staking contract
    dai_starting = dai.balanceOf(dai_whale)
    dai.approve(zap, 2**256 - 1, {"from": dai_whale})

    # can't deposit into a contract that isn't in our registry
    with brownie.reverts("staking pool doesn't exist"):
        zap.zapIn(yvdai, dai_amount, {"from": dai_whale})

    # can't zap into zero address (vault deposit() step will fail)
    with brownie.reverts():
        zap.zapIn(ZERO_ADDRESS, dai_amount, {"from": dai_whale})

    # Add our staking contract to our registry
    registry.addStakingPool(yvdai_pool, yvdai, False, {"from": gov})

    # need to pretend to stakeFor directly from zap contract to hit the require
    with brownie.reverts("Cannot stake 0"):
        yvdai_pool.stakeFor(dai_whale, 0, {"from": zap})

    # zap in, but can't zap zero
    with brownie.reverts():
        zap.zapIn(yvdai, 0, {"from": dai_whale})
    zap.zapIn(yvdai, dai_amount, {"from": dai_whale})
    balance = yvdai_pool.balanceOf(dai_whale)
    assert balance > 0
    print("Staked balance of yvDAI, should be ~1000:", balance / 1e18)

    # check that our zap has zero balance
    zap_balance = yvdai_pool.balanceOf(zap)
    assert zap_balance == 0
    with brownie.reverts():
        yvdai_pool.withdraw(100e18, {"from": zap})

    # whale sends directly to pool, gov notifies rewards
    yvop.transfer(yvdai_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    yvdai_pool.notifyRewardAmount(100e18, {"from": gov})

    # no problem to zap in a bit more
    chain.sleep(1)
    chain.mine(1)
    zap.zapIn(yvdai, dai_amount, {"from": dai_whale})

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, get reward
    earned = yvdai_pool.earned(dai_whale)
    assert earned > 0
    yvdai_pool.getReward({"from": dai_whale})
    assert pytest.approx(yvop.balanceOf(dai_whale), rel=RELATIVE_APPROX) == earned

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # exit, check that we have the same principal and earned more rewards
    yvdai_pool.exit({"from": dai_whale})
    yvdai.withdraw({"from": dai_whale})
    assert pytest.approx(dai_starting, rel=RELATIVE_APPROX) == dai.balanceOf(dai_whale)
    assert yvop.balanceOf(dai_whale) > earned

    # check that no one else can use stakeFor (even gov!)
    yvdai.approve(yvdai_pool, 2**256 - 1, {"from": gov})
    yvdai.transfer(gov, 100e18, {"from": yvdai_whale})
    with brownie.reverts("Only zap contract"):
        yvdai_pool.stakeFor(gov, 100e18, {"from": gov})

    # zero address for registry will revert on zap in
    zap.setPoolRegistry(ZERO_ADDRESS, {"from": gov})
    with brownie.reverts():
        zap.zapIn(yvdai, dai_amount, {"from": dai_whale})


def test_registry(
    gov,
    yvdai,
    yvdai_amount,
    yvdai_whale,
    dai,
    dai_amount,
    dai_whale,
    yvusdc,
    yvusdc_amount,
    yvusdc_whale,
    yvop,
    yvop_whale,
    registry,
    zap,
    yvdai_pool,
    yvusdc_pool,
    RELATIVE_APPROX,
    StakingRewards,
    strategist,
):
    # check that dai isn't registered yet
    assert registry.isRegistered(dai.address) == False

    # not just anyone can add a pool
    with brownie.reverts():
        registry.addStakingPool(yvdai_pool, yvdai, False, {"from": strategist})

    # Add our staking contract to our registry
    registry.addStakingPool(yvdai_pool, yvdai, False, {"from": gov})
    assert registry.isRegistered(yvdai.address) == True

    # can't have a mismatch in tokens
    with brownie.reverts():
        registry.addStakingPool(yvusdc_pool, yvdai, False, {"from": gov})

    # can't replace a pool that hasn't been added yet
    with brownie.reverts():
        registry.addStakingPool(yvusdc_pool, yvusdc, True, {"from": gov})

    # can't add another pool for the same underlying without replacing
    yvdai_pool_too = gov.deploy(
        StakingRewards,
        gov.address,
        gov.address,
        yvop.address,
        yvdai.address,
        zap.address,
    )
    with brownie.reverts():
        registry.addStakingPool(yvdai_pool_too, yvdai, False, {"from": gov})

    # check that the correct pools are showing up
    assert registry.stakingPool(yvdai.address) == yvdai_pool.address
    assert registry.isStakingPoolEndorsed(yvdai_pool) == True
    assert registry.isStakingPoolEndorsed(yvdai_pool_too) == False

    # replace instead of adding
    registry.addStakingPool(yvdai_pool_too, yvdai, True, {"from": gov})
    assert registry.stakingPool(yvdai.address) == yvdai_pool_too.address

    # make sure we can't add one with incorrect gov
    yvdai_pool_three = strategist.deploy(
        StakingRewards,
        strategist.address,
        strategist.address,
        yvop.address,
        yvdai.address,
        zap.address,
    )

    with brownie.reverts():
        registry.addStakingPool(yvdai_pool_three, yvdai, True, {"from": gov})

    # zero address reverts
    with brownie.reverts():
        registry.addStakingPool(ZERO_ADDRESS, yvdai, True, {"from": gov})

    with brownie.reverts():
        registry.addStakingPool(yvdai_pool_three, ZERO_ADDRESS, True, {"from": gov})

    # check our endorsing is working properly
    assert registry.isStakingPoolEndorsed(yvdai_pool_three) == False
    assert registry.isStakingPoolEndorsed(yvdai_pool_too) == True
    assert registry.isStakingPoolEndorsed(yvdai_pool) == False

    # make sure our length is what we expect for tokens
    assert registry.numTokens() == 1
    assert registry.isRegistered(yvusdc.address) == False
    assert registry.isStakingPoolEndorsed(yvusdc_pool) == False

    # add yvusdc
    registry.addStakingPool(yvusdc_pool, yvusdc, False, {"from": gov})
    assert registry.numTokens() == 2
    assert registry.isStakingPoolEndorsed(yvusdc_pool) == True
    assert registry.isRegistered(yvusdc.address) == True

    # check our tokens view
    assert registry.tokens(0) == yvdai.address
    assert registry.tokens(1) == yvusdc.address
