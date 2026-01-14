pragma solidity ^0.8.20;

import {Test} from "forge-std/Test.sol";

import {ContentEscrow} from "../src/ContentEscrow.sol";
import {MockUSDC3009} from "../src/MockUSDC3009.sol";

contract ContentEscrowTest is Test {
    MockUSDC3009 private token;
    ContentEscrow private escrow;

    address private user = address(0x1111);
    address private creator = address(0x2222);
    address private platform = address(0x3333);

    function setUp() public {
        token = new MockUSDC3009();
        escrow = new ContentEscrow(address(token), platform);
    }

    function test_streamWithAuthorization_splits90_10() public {
        token.mint(user, 1_000_000);

        uint256 amount = 1_000_000;
        bytes memory sig = hex"";
        bytes32 nonce = bytes32(uint256(123));

        escrow.streamWithAuthorization(user, creator, amount, 0, type(uint256).max, nonce, sig);

        assertEq(token.balanceOf(user), 0);
        assertEq(token.balanceOf(address(escrow)), amount);
        assertEq(escrow.creatorBalances(creator), 900_000);
        assertEq(escrow.platformBalance(), 100_000);
    }

    function test_streamWithAuthorization_accumulates() public {
        token.mint(user, 2_000_000);

        bytes memory sig = hex"";
        escrow.streamWithAuthorization(user, creator, 1_000_000, 0, type(uint256).max, bytes32(uint256(1)), sig);
        escrow.streamWithAuthorization(user, creator, 1_000_000, 0, type(uint256).max, bytes32(uint256(2)), sig);

        assertEq(token.balanceOf(user), 0);
        assertEq(token.balanceOf(address(escrow)), 2_000_000);
        assertEq(escrow.creatorBalances(creator), 1_800_000);
        assertEq(escrow.platformBalance(), 200_000);
    }

    function test_withdrawCreator_transfers_and_zeroes_balance() public {
        token.mint(user, 1_000_000);

        escrow.streamWithAuthorization(user, creator, 1_000_000, 0, type(uint256).max, bytes32(uint256(1)), hex"");

        assertEq(token.balanceOf(creator), 0);
        vm.prank(creator);
        escrow.withdrawCreator();

        assertEq(token.balanceOf(creator), 900_000);
        assertEq(escrow.creatorBalances(creator), 0);
        assertEq(token.balanceOf(address(escrow)), 100_000);
    }

    function test_withdrawPlatform_transfers_and_zeroes_balance() public {
        token.mint(user, 1_000_000);

        escrow.streamWithAuthorization(user, creator, 1_000_000, 0, type(uint256).max, bytes32(uint256(1)), hex"");

        assertEq(token.balanceOf(platform), 0);
        escrow.withdrawPlatform();

        assertEq(token.balanceOf(platform), 100_000);
        assertEq(escrow.platformBalance(), 0);
        assertEq(token.balanceOf(address(escrow)), 900_000);
    }

    function test_withdrawCreator_reverts_on_zero_balance() public {
        vm.prank(creator);
        vm.expectRevert(ContentEscrow.NothingToWithdraw.selector);
        escrow.withdrawCreator();
    }

    function test_withdrawPlatform_reverts_on_zero_balance() public {
        vm.expectRevert(ContentEscrow.NothingToWithdraw.selector);
        escrow.withdrawPlatform();
    }
}
