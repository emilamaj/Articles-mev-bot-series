//SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8;

contract UniswapFlashQuery {
    function getReservesByPairsAsm(address[] calldata _pairs) external view returns (bytes32[] memory) {
        // Note that the array has been flattened, handling 2D arrays in assembly is much more complex.
        bytes32[] memory result = new bytes32[](_pairs.length * 3);

        assembly {
            // Size of the return data (reserve0, reserve1, blockTimestampLast)
            let size := 0x60 // Values are not packed, so 3 * 32 bytes = 3 * 0x20 = 0x60 bytes
            
            // Allocate memory for the function selector
            let callData := mload(0x40)
            mstore(callData, 0x0902f1ac00000000000000000000000000000000000000000000000000000000) // 4-byte function selector of the getReserves() function. Note the padding to the right.
            mstore(0x40, add(callData, 0x04)) // Update the free memory pointer

            for { let i := 0 } lt(i, _pairs.length) { i := add(i, 1) } {
                // Load the pair address from the calldata
                let pair := calldataload(add(_pairs.offset, mul(i, 0x20)))
                    
                // Call the getReserves() function, write the return data to the preallocated memory for the "result" array.
                let success := staticcall(gas(), pair, callData, 0x04, add(add(result, 0x20),mul(i, size)), size)
            }

            // Update the free memory pointer
            mstore(0x40, add(mload(0x40), mul(_pairs.length, size)))
        }

        return result;
    }
}