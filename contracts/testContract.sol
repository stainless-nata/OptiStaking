// SPDX-License-Identifier: AGPL-3.0
pragma solidity ^0.5.16;

import "@openzeppelin/contracts/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20Detailed.sol";
import "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

contract testContract {
    using SafeMath for uint256;

    function test(
        uint256 first,
        uint256 second,
        uint256 third,
        uint256 fourth,
        uint256 fifth
    ) public view returns (uint256) {
        return first.add(second.sub(third).mul(fourth).mul(1e18).div(fifth));
    }
}
