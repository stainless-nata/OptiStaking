import brownie
from brownie import ZERO_ADDRESS, chain, interface
import pytest


def test_old_live_zap_fails(
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
    old_live_zap,
    yvdai_pool,
    yvdai_pool_live,
    yvusdc_pool,
    RELATIVE_APPROX,
):
    # Approve and zap into to the staking contract
    dai_starting = dai.balanceOf(dai_whale)
    dai.approve(old_live_zap, 2**256 - 1, {"from": dai_whale})

    # oChad lowers deposit yvdai, fucking rude!
    yvdai.setDepositLimit(yvdai.totalAssets() + 1e18, {"from": gov})

    # zap in, but we get rugged, only have 1 DAI in the vault :(
    old_live_zap.zapIn(yvdai, dai_amount, {"from": dai_whale})
    balance = yvdai_pool_live.balanceOf(dai_whale)
    assert balance < 1e18
    print("Staked balance of yvDAI, should be <1:", balance / 1e18)

    # our zap should now have DAI stuck in it
    stuck_dai = dai.balanceOf(old_live_zap)
    assert stuck_dai > 0
    print("Stuck DAI:", stuck_dai / 1e18)


def test_new_zap_works(
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
    new_zap,
    yvdai_pool,
    yvusdc_pool,
    yvdai_pool_live,
    RELATIVE_APPROX,
):
    # Approve and zap into to the staking contract
    dai_starting = dai.balanceOf(dai_whale)
    dai.approve(new_zap, 2**256 - 1, {"from": dai_whale})

    # oChad lowers deposit yvdai, fucking rude!
    yvdai.setDepositLimit(yvdai.totalAssets() + 100e18, {"from": gov})

    # update our zap contract
    yvdai_pool_live.setZapContract(new_zap, {"from": gov})

    # zap in, but it should fail
    with brownie.reverts():
        new_zap.zapIn(yvdai, dai_amount, {"from": dai_whale})
    assert dai.balanceOf(dai_whale) == dai_starting
