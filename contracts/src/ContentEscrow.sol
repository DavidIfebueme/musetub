pragma solidity ^0.8.20;

interface IERC20Like {
    function transfer(address to, uint256 value) external returns (bool);
}

interface IERC3009Like {
    function receiveWithAuthorization(
        address from,
        address to,
        uint256 value,
        uint256 validAfter,
        uint256 validBefore,
        bytes32 nonce,
        bytes calldata signature
    ) external;
}

contract ContentEscrow {
    error ZeroAddress();
    error ZeroAmount();
    error NothingToWithdraw();
    error TokenTransferFailed();

    event Streamed(address indexed user, address indexed creator, uint256 amount, uint256 creatorShare, uint256 platformShare);
    event CreatorWithdrawn(address indexed creator, uint256 amount);
    event PlatformWithdrawn(address indexed to, uint256 amount);

    address public immutable usdc;
    address public platformWithdrawAddress;

    mapping(address => uint256) public creatorBalances;
    uint256 public platformBalance;

    constructor(address usdc_, address platformWithdrawAddress_) {
        if (usdc_ == address(0) || platformWithdrawAddress_ == address(0)) revert ZeroAddress();
        usdc = usdc_;
        platformWithdrawAddress = platformWithdrawAddress_;
    }

    function setPlatformWithdrawAddress(address newPlatformWithdrawAddress) external {
        if (newPlatformWithdrawAddress == address(0)) revert ZeroAddress();
        platformWithdrawAddress = newPlatformWithdrawAddress;
    }

    function streamWithAuthorization(
        address user,
        address creator,
        uint256 amount,
        uint256 validAfter,
        uint256 validBefore,
        bytes32 nonce,
        bytes calldata signature
    ) external {
        if (user == address(0) || creator == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();

        IERC3009Like(usdc).receiveWithAuthorization(user, address(this), amount, validAfter, validBefore, nonce, signature);

        uint256 creatorShare = (amount * 90) / 100;
        uint256 platformShare = amount - creatorShare;

        creatorBalances[creator] += creatorShare;
        platformBalance += platformShare;

        emit Streamed(user, creator, amount, creatorShare, platformShare);
    }

    function withdrawCreator() external {
        uint256 amount = creatorBalances[msg.sender];
        if (amount == 0) revert NothingToWithdraw();
        creatorBalances[msg.sender] = 0;

        if (!IERC20Like(usdc).transfer(msg.sender, amount)) revert TokenTransferFailed();
        emit CreatorWithdrawn(msg.sender, amount);
    }

    function withdrawPlatform() external {
        uint256 amount = platformBalance;
        if (amount == 0) revert NothingToWithdraw();
        platformBalance = 0;

        address to = platformWithdrawAddress;
        if (!IERC20Like(usdc).transfer(to, amount)) revert TokenTransferFailed();
        emit PlatformWithdrawn(to, amount);
    }
}
