pragma solidity ^0.8.20;

contract MockUSDC3009 {
    error InsufficientBalance();

    mapping(address => uint256) public balanceOf;

    function mint(address to, uint256 amount) external {
        balanceOf[to] += amount;
    }

    function transfer(address to, uint256 value) external returns (bool) {
        uint256 fromBal = balanceOf[msg.sender];
        if (fromBal < value) revert InsufficientBalance();
        unchecked {
            balanceOf[msg.sender] = fromBal - value;
        }
        balanceOf[to] += value;
        return true;
    }

    function receiveWithAuthorization(
        address from,
        address to,
        uint256 value,
        uint256,
        uint256,
        bytes32,
        bytes calldata
    ) external {
        uint256 fromBal = balanceOf[from];
        if (fromBal < value) revert InsufficientBalance();
        unchecked {
            balanceOf[from] = fromBal - value;
        }
        balanceOf[to] += value;
    }
}
