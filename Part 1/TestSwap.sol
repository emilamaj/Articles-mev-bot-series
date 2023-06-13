// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0; // Any Solidity 0.8.x version

interface IUniswapV2Pair { // Using interfaces has the same role as using ABIs in web3.py
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

interface IWETH { // To simply the code, we only include the functions we use in the interface declaration
    function deposit() external payable;
}

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
}

contract TestSwap {
    // Store the addresses used as constants for readability. This does not cost any gas.
    address constant USDT = 0xdAC17F958D2ee523a2206206994597C13D831ec7;
    address constant WETH = 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2;
    address constant UNI_PAIR = 0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852;

    // Define the function the will be called by web3.py
    function startSwap(uint usdtOut) external payable {// External specifies that this function is called from outside this contract. The payable keyword makes the function capable of receive ETH when called.
        // Wrap the ETH received in the transaction into WETH. The amount of ETH received is available in msg.value
        // We call the WETH contract's deposit() function and forward the same amount of ETH we received in the transaction
        IWETH(WETH).deposit{value: msg.value}(); // The {value: msg.value} syntax is used to forward ETH to a contract when calling it. The parameters are still between parentheses (here there are none).

        // Now that we have WETH, we can send it to the Uniswap Pair contract.
        IERC20(WETH).transfer(UNI_PAIR, msg.value); // We use the ERC20 transfer() function. The amount of WETH is the same as the ETH received.

        // Just like with the WETH contract, we enclose the address with the interface we want to use, and call the function of interest.
        // Remember that USDT is the token1 of the pair. We don't want to swap out any ETH, so we pass 0 as the first parameter.
        // To specify the current contract as the recipient of the output, we could have used address(this) instead of msg.sender. Here we sent the output to the address that called the current transaction.
        IUniswapV2Pair(UNI_PAIR).swap(0, usdtOut, msg.sender, new bytes(0)); // The last parameter is the data parameter, which we don't use here. We pass an empty bytes array.
    }
}