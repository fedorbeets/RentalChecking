// In remix: compile EqualityTest.sol, not pairing.sol
pragma solidity ^0.4.19;

// Input array loop and inline assembly taken from Christian Reitwiessner,
// from https://gist.github.com/chriseth/f9be9d9391efc5beb9704255a8e2989d

// This file is MIT Licensed.
//
// Copyright 2018 Fedor Beets
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

contract pairing_check_token_stored {

    event Result(bool result);
    
    
    
//    struct G1Point {
//		uint X;
//		uint Y;
//	}
	// Encoding of field elements is: X[0] * z + X[1]
//	struct G2Point {
//		uint[2] X;
//		uint[2] Y;
//	}

//    event Points(uint pointX, uint pointY);

//    event PointG2(uint pointX1,
//                uint pointX2,
//                uint pointY1,
//                uint pointY2);
    // Token part of equality test
    uint[] private g2_x_i;
    uint[] private g2_x_r;
    uint[] private g2_y_i;
    uint[] private g2_y_r;

    // Instantiate the contract and store the token part of the equations.
    function pairing_check_token_stored(
        uint[] _g2_x_i, uint[] _g2_x_r, uint[] _g2_y_i, uint[] _g2_y_r
        ) public {
            g2_x_i = _g2_x_i;
            g2_x_r = _g2_x_r;
            g2_y_i = _g2_y_i;
            g2_y_r = _g2_y_r;
        }


    // To test for equality:
    // First N points must be "left side of equation"
    // Next N+1 points must be "right side of equation"
    // Must include equal amounts of points in G1 as in G2
    // Assume negation has been done off-chain
    // Requires less than 255 points
    function test_equality(uint[] g1points_x, uint[] g1points_y
        ) public returns (bool){
            assert(g1points_x.length == g2_x_i.length);
            // Otherwise loop does not terminate
            assert(g1points_x.length < 255);
            //Must have an equal amount of points in G1,G2

            //Do pairing, store result in memory and emit as event
            
        /// @return the result of computing the pairing check
	    /// e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
	    /// For example pairing([P1(), P1().negate()], [P2(), P2()]) should
	    /// return true.
		uint elements = g1points_x.length;
		uint inputSize = elements * 6;
		uint[] memory input = new uint[](inputSize);
		//Can increase by 6 every time, then don't need to multiply
		for (uint j = 0; j < elements; j++)
		{
			input[j * 6 + 0] = g1points_x[j];
			input[j * 6 + 1] = g1points_y[j];
			input[j * 6 + 2] = g2_x_i[j];
			input[j * 6 + 3] = g2_x_r[j];
			input[j * 6 + 4] = g2_y_i[j];
			input[j * 6 + 5] = g2_y_r[j];
			//PointG1(p1[i].X, p1[i].Y);
			//PointG2(p2[i].X, p2[i].Y);
		}
		uint[1] memory out;
		bool success;
		assembly {
			success := call(sub(gas, 2000), 8, 0, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
			// Use "invalid" to make gas estimation work
			switch success case 0 { invalid }
		}
		require(success);
		// Re-use success boolean
		success =  out[0] != 0; 
        Result(success); //emit event
        return success;
        }
        

}
