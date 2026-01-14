pragma solidity ^0.8.20;

import {Script} from "forge-std/Script.sol";

import {ContentEscrow} from "../src/ContentEscrow.sol";

contract DeployContentEscrow is Script {
    function run() external returns (ContentEscrow deployed) {
        address usdc = vm.envAddress("USDC_ADDRESS");
        address platformWithdrawAddress = vm.envAddress("PLATFORM_WITHDRAW_ADDRESS");

        vm.startBroadcast();
        deployed = new ContentEscrow(usdc, platformWithdrawAddress);
        vm.stopBroadcast();

        return deployed;
    }
}
