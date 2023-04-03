import pytest
from brownie import config
from brownie import Contract, interface


# Function scoped isolation fixture to enable xdist.
# Snapshots the chain before each test and reverts after test completion.
@pytest.fixture(scope="function", autouse=True)
def shared_setup(fn_isolation):
    pass


@pytest.fixture
def gov(accounts):
    yield accounts.at("0xF5d9D6133b698cE29567a90Ab35CfB874204B3A7", force=True)


@pytest.fixture
def user(accounts):
    yield accounts[0]


@pytest.fixture
def rewards(accounts):
    yield accounts[1]


@pytest.fixture
def guardian(accounts):
    yield accounts[2]


@pytest.fixture
def management(accounts):
    yield accounts[3]


@pytest.fixture
def strategist(accounts):
    yield accounts.at("0xC6387E937Bcef8De3334f80EDC623275d42457ff", force=True)


@pytest.fixture
def keeper(accounts):
    yield accounts[5]


@pytest.fixture
def yvdai():
    token_address = "0x65343F414FFD6c97b0f6add33d16F6845Ac22BAc"  # this is our test staking vault (yvDAI 0.4.5)
    yield interface.IVaultFactory045(token_address)


@pytest.fixture
def yvdai_amount(yvdai):
    yvdai_amount = 100 * 10 ** yvdai.decimals()
    yield yvdai_amount


@pytest.fixture
def yvdai_whale(accounts):
    yvdai_whale = accounts.at(
        "0x8651bA8416F97a27147E58423240cc786f5A0D32", force=True
    )  # ~2900 yvDAI
    yield yvdai_whale


@pytest.fixture
def yvusdc():
    token_address = "0xaD17A225074191d5c8a37B50FdA1AE278a2EE6A2"  # this is our test staking vault (yvUSDC 0.4.5)
    yield interface.IVaultFactory045(token_address)


@pytest.fixture
def yvusdc_amount(yvusdc):
    yvusdc_amount = 600 * 10 ** yvusdc.decimals()
    yield yvusdc_amount


@pytest.fixture
def yvusdc_whale(accounts):
    yvusdc_whale = accounts.at(
        "0x2EBd8C6325591711280f2a735bc189509620349B", force=True
    )  # ~1500 yvusdc
    yield yvusdc_whale


@pytest.fixture
def yvop():
    token_address = "0x7D2382b1f8Af621229d33464340541Db362B4907"  # $OP yVault
    yield interface.IVaultFactory045(token_address)


@pytest.fixture
def yvop_amount(yvop):
    yvop_amount = 500 * 10 ** yvop.decimals()
    yield yvop_amount


@pytest.fixture
def yvop_whale(accounts):
    yvop_whale = accounts.at(
        "0xE880F32E33061919D09811EeE00Ee94392cd4fde", force=True
    )  # ~2000 yvop
    yield yvop_whale


@pytest.fixture
def dai():
    token_address = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"  # DAI
    yield interface.IERC20(token_address)


@pytest.fixture
def dai_amount(yvdai):
    dai_amount = 1_000 * 10 ** yvdai.decimals()
    yield dai_amount


@pytest.fixture
def dai_whale(accounts):
    dai_whale = accounts.at(
        "0x7B7B957c284C2C227C980d6E2F804311947b84d0", force=True
    )  # ~3m DAI
    yield dai_whale


@pytest.fixture
def registry(StakingRewardsRegistry, gov):
    registry = gov.deploy(StakingRewardsRegistry)
    registry.setPoolEndorsers(gov, True, {"from": gov})
    registry.setApprovedPoolOwner(gov, True, {"from": gov})
    yield registry


@pytest.fixture
def zap(StakingRewardsZap, gov, registry):
    zap = gov.deploy(StakingRewardsZap, registry.address)
    yield zap


@pytest.fixture
def yvdai_pool(StakingRewards, gov, registry, yvdai, yvop, zap):
    yvdai_pool = gov.deploy(
        StakingRewards,
        gov.address,
        gov.address,
        yvop.address,
        yvdai.address,
        zap.address,
    )
    yield yvdai_pool


# @pytest.fixture
# def yvdai_pool_clonable(StakingRewardsClonable, gov, registry, yvdai, yvop, zap):
#     yvdai_pool_clonable = gov.deploy(
#         StakingRewardsClonable,
#         gov.address,
#         gov.address,
#         yvop.address,
#         yvdai.address,
#         zap.address,
#     )
#     yield yvdai_pool_clonable


@pytest.fixture
def yvusdc_pool(StakingRewards, gov, registry, yvusdc, yvop, zap):
    yvusdc_pool = gov.deploy(
        StakingRewards,
        gov.address,
        gov.address,
        yvop.address,
        yvusdc.address,
        zap.address,
    )
    yield yvusdc_pool


@pytest.fixture(scope="session")
def RELATIVE_APPROX():
    yield 1e-2
