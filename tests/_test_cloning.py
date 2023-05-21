import brownie
from brownie import ZERO_ADDRESS

# test cloning our strategy, make sure the cloned strategy still works just fine by sending funds to it
def test_cloning(
    StakingRewardsClonable,
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
    yvdai_pool_clonable,
    yvusdc_pool,
    dai,
    dai_whale,
    dai_amount,
):

    # Shouldn't be able to call initialize again
    with brownie.reverts():
        yvdai_pool_clonable.initialize(
            gov.address,
            yvop.address,
            yvdai.address,
            zap.address,
            {"from": gov},
        )
    tx = yvdai_pool_clonable.cloneStakingPool(
        gov.address,
        gov.address,
        yvop.address,
        yvdai.address,
        zap.address,
        {"from": gov},
    )

    new_staking_pool = StakingRewardsClonable.at(tx.return_value)

    # Shouldn't be able to call initialize again
    with brownie.reverts():
        new_staking_pool.initialize(
            gov.address,
            yvop.address,
            yvdai.address,
            zap.address,
            {"from": gov},
        )

    ## shouldn't be able to clone a clone
    with brownie.reverts():
        new_staking_pool.cloneStakingPool(
            gov.address,
            gov.address,
            yvop.address,
            yvdai.address,
            zap.address,
            {"from": gov},
        )

    # must accept ownnership from gov
    assert new_staking_pool.owner() != gov.address
    new_staking_pool.acceptOwnership({"from": gov})
    assert new_staking_pool.owner() == gov.address

    # Approve and deposit to the staking contract
    yvdai_starting = yvdai.balanceOf(yvdai_whale)
    yvdai.approve(new_staking_pool, 2**256 - 1, {"from": yvdai_whale})
    new_staking_pool.stake(yvdai_amount, {"from": yvdai_whale})
    assert new_staking_pool.balanceOf(yvdai_whale) == yvdai_amount

    # can't stake zero
    with brownie.reverts("Cannot stake 0"):
        new_staking_pool.stake(0, {"from": yvdai_whale})

    # whale sends directly to pool, gov notifies rewards
    yvop.transfer(new_staking_pool, yvop.balanceOf(yvop_whale), {"from": yvop_whale})
    new_staking_pool.notifyRewardAmount(100e18, {"from": gov})

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # check claimable earnings, get reward
    earned = new_staking_pool.earned(yvdai_whale)
    assert earned > 0
    new_staking_pool.getReward({"from": yvdai_whale})
    assert yvop.balanceOf(yvdai_whale) >= earned
    assert new_staking_pool.getRewardForDuration({"from": yvdai_whale}) > 0

    # sleep to gain some earnings
    chain.sleep(86400)
    chain.mine(1)

    # can't withdraw zero
    with brownie.reverts("Cannot withdraw 0"):
        new_staking_pool.withdraw(0, {"from": yvdai_whale})

    # exit, check that we have the same principal and earned more rewards
    new_staking_pool.exit({"from": yvdai_whale})
    assert yvdai_starting == yvdai.balanceOf(yvdai_whale)
    assert yvop.balanceOf(yvdai_whale) > earned

    # check our setters
    with brownie.reverts():
        new_staking_pool.setRewardsDuration(100e18, {"from": gov})
    with brownie.reverts():
        new_staking_pool.setZapContract(ZERO_ADDRESS, {"from": gov})
    new_staking_pool.setZapContract(zap, {"from": gov})

    # sleep to get past our rewards window
    chain.sleep(86400 * 6)
    new_staking_pool.setRewardsDuration(86400 * 14, {"from": gov})
