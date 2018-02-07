// In remix: compile EqualityTest.sol, not pairing.sol
pragma solidity ^0.4.19;

contract pairing_check {

    event Result(bool result);

    event Integer(uint number);

    event Points(uint pointX, uint pointY);

    event PointG2(uint pointX1,
                uint pointX2,
                uint pointY1,
                uint pointY2);


    function testG1() public returns (Pairing.G1Point){
        Pairing.G1Point memory point1 = Pairing.P1();
        point1 = Pairing.mul(point1, 0);
        Points(point1.X, point1.Y);
        return point1;
    }

    function testPairing() public returns (string){
        Pairing.G1Point memory point1 = testG1();
        Pairing.G2Point memory point2 = Pairing.P2();
        // output to event
        PointG2(point2.X[0], point2.X[1], point2.Y[0], point2.Y[1]);

        Pairing.G1Point[] memory p1 = new Pairing.G1Point[](1);
		Pairing.G2Point[] memory p2 = new Pairing.G2Point[](1);
		p1[0] = point1;
		p2[0] = point2;
        Result(Pairing.pairing(p1,p2));
        return "Return Value";
    }

    function testPairing2() public returns (bool){
        Pairing.G2Point memory fiveTimesP2 = Pairing.G2Point(
			[4540444681147253467785307942530223364530218361853237193970751657229138047649, 20954117799226682825035885491234530437475518021362091509513177301640194298072],
			[11631839690097995216017572651900167465857396346217730511548857041925508482915, 21508930868448350162258892668132814424284302804699005394342512102884055673846]
		);
		// The prime p in the base field F_p for G1
		uint p = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
		Pairing.G1Point[] memory g1points = new Pairing.G1Point[](2);
		Pairing.G2Point[] memory g2points = new Pairing.G2Point[](2);
// 			// check e(5 P1, P2)e(-P1, 5 P2) == 1
		g1points[0] = Pairing.mul(Pairing.P1(), 5);
		g1points[1] = Pairing.P1();
		g1points[1].Y = p - g1points[1].Y;
		g2points[0] = Pairing.P2();
		g2points[1] = fiveTimesP2;
		if (!Pairing.pairing(g1points, g2points))
			return false;
		// check e(P1, P2)e(-P1, P2) == 0
		g1points[0] = Pairing.P1();
		g1points[1] = Pairing.negate(Pairing.P1());
		g2points[0] = Pairing.P2();
		g2points[1] = Pairing.P2();
		if (!Pairing.pairing(g1points, g2points))
			return false;
        return true;
    }


    // To test for equality:
    // First N points must be "left side of equation"
    // Next N+1 points must be "right side of equation"
    function test_simple(uint[] g1points_x, uint[] g1points_y,
        uint[] g2_x_i, uint[] g2_x_r, uint[] g2_y_i, uint[] g2_y_r
        ) public returns (bool){
            //Must have an equal amount of points in G1,G2
            require(g1points_x.length == g1points_y.length && g2_x_i.length == g2_y_i.length
                && g2_x_i.length == g2_x_r.length && g2_x_i.length == g2_y_r.length
                && g1points_x.length == g2_x_i.length);


            // Container for all points to be paired
            Pairing.G1Point[] memory pointsG1 = new Pairing.G1Point[](g1points_x.length);
            Pairing.G2Point[] memory pointsG2 = new Pairing.G2Point[](g1points_x.length);

            //uint[2] memory g2_x_ir;
            //uint[2] memory g2_y_ir;
            //Stitch points together from uints
            for(uint8 i=0; i< g1points_x.length; i++){

                //Assume negation has been done off-chain
                pointsG1[i] = Pairing.G1Point(g1points_x[i], g1points_y[i]);

                //g2_x_ir[0] = g2_x_i[i];
                //g2_x_ir[1] = g2_x_r[i];

                //g2_y_ir[0] = g2_y_i[i];
                //g2_y_ir[1] = g2_y_r[i];
                // If you make points out of arrays in memory, then anytime you change that array to allocate
                // a new point, all of your old points change as well.
                pointsG2[i] = Pairing.G2Point([g2_x_i[i], g2_x_r[i]],[g2_y_i[i],g2_y_r[i]]);

                //Log points as events
                //Points(pointsG1[i].X, pointsG1[i].Y);
                //PointG2(pointsG2[i].X[0], pointsG2[i].X[1], pointsG2[i].Y[0], pointsG2[i].Y[1]);
            }
            //Contract fails to execute transaction when pairing instruction is included.
            // Possibly runs out of gas
            // May also just be throwing an exception
            // https://ethereum.stackexchange.com/questions/28077/how-do-i-detect-a-failed-transaction-after-the-byzantium-fork-as-the-revert-opco
            // This link says it is because of a thrown exception
            // Transaction is trying to call non-existant opcode 0xfe (opcode not specified in yellowpaper)
            //Do pairing, store result in memory and emit as event
            //Do pairing, store result in memory and emit as event

            bool result = Pairing.pairing(pointsG1, pointsG2);
            Result(result); //emit event
            //Result(true);
            return result;

        }

}
// From https://gist.github.com/chriseth/f9be9d9391efc5beb9704255a8e2989d
// This file is MIT Licensed.
//
// Copyright 2017 Christian Reitwiessner
// Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
// The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

library Pairing {

    event PointG1(uint X,
		uint Y);

    event PointG2(uint[2] X,
		uint[2] Y);

	struct G1Point {
		uint X;
		uint Y;
	}
	// Encoding of field elements is: X[0] * z + X[1]
	struct G2Point {
		uint[2] X;
		uint[2] Y;
	}
	/// @return the generator of G1
	function P1() internal returns (G1Point) {
		return G1Point(1, 2);
	}
	/// @return the generator of G2
	function P2() internal returns (G2Point) {
		return G2Point(
			[11559732032986387107991004021392285783925812861821192530917403151452391805634,
			 10857046999023057135944570762232829481370756359578518086990519993285655852781],
			[4082367875863433681332203403145435568316851327593401208105741076214120093531,
			 8495653923123431417604973247489272438418190587263600148770280649306958101930]
		);
	}
	/// @return the negation of p, i.e. p.add(p.negate()) should be zero.
	function negate(G1Point p) internal returns (G1Point) {
		// The prime q in the base field F_q for G1
		uint q = 21888242871839275222246405745257275088696311157297823662689037894645226208583;
		if (p.X == 0 && p.Y == 0)
			return G1Point(0, 0);
		return G1Point(p.X, q - (p.Y % q));
	}
	/// @return the sum of two points of G1
	function add(G1Point p1, G1Point p2) internal returns (G1Point r) {
		uint[4] memory input;
		input[0] = p1.X;
		input[1] = p1.Y;
		input[2] = p2.X;
		input[3] = p2.Y;
		bool success;
		assembly {
			success := call(sub(gas, 2000), 6, 0, input, 0xc0, r, 0x60)
			// Use "invalid" to make gas estimation work
			switch success case 0 { invalid }
		}
		require(success);
	}
	/// @return the product of a point on G1 and a scalar, i.e.
	/// p == p.mul(1) and p.add(p) == p.mul(2) for all points p.
	function mul(G1Point p, uint s) internal returns (G1Point r) {
		uint[3] memory input;
		input[0] = p.X;
		input[1] = p.Y;
		input[2] = s;
		bool success;
		assembly {
			success := call(sub(gas, 2000), 7, 0, input, 0x80, r, 0x60)
			// Use "invalid" to make gas estimation work
			switch success case 0 { invalid }
		}
		require (success);
	}
	/// @return the result of computing the pairing check
	/// e(p1[0], p2[0]) *  .... * e(p1[n], p2[n]) == 1
	/// For example pairing([P1(), P1().negate()], [P2(), P2()]) should
	/// return true.
	function pairing(G1Point[] p1, G2Point[] p2) internal returns (bool) {
		require(p1.length == p2.length);
		uint elements = p1.length;
		uint inputSize = elements * 6;
		uint[] memory input = new uint[](inputSize);
		for (uint i = 0; i < elements; i++)
		{
			input[i * 6 + 0] = p1[i].X;
			input[i * 6 + 1] = p1[i].Y;
			input[i * 6 + 2] = p2[i].X[0];
			input[i * 6 + 3] = p2[i].X[1];
			input[i * 6 + 4] = p2[i].Y[0];
			input[i * 6 + 5] = p2[i].Y[1];
			PointG1(p1[i].X, p1[i].Y);
			PointG2(p2[i].X, p2[i].Y);
		}
		uint[1] memory out;
		bool success;
		assembly {
			success := call(sub(gas, 2000), 8, 0, add(input, 0x20), mul(inputSize, 0x20), out, 0x20)
			// Use "invalid" to make gas estimation work
			switch success case 0 { invalid }
		}
		require(success);
		return out[0] != 0;
	}
	/// Convenience method for a pairing check for two pairs.
	function pairingProd2(G1Point a1, G2Point a2, G1Point b1, G2Point b2) internal returns (bool) {
		G1Point[] memory p1 = new G1Point[](2);
		G2Point[] memory p2 = new G2Point[](2);
		p1[0] = a1;
		p1[1] = b1;
		p2[0] = a2;
		p2[1] = b2;
		return pairing(p1, p2);
	}
	/// Convenience method for a pairing check for three pairs.
	function pairingProd3(
			G1Point a1, G2Point a2,
			G1Point b1, G2Point b2,
			G1Point c1, G2Point c2
	) internal returns (bool) {
		G1Point[] memory p1 = new G1Point[](3);
		G2Point[] memory p2 = new G2Point[](3);
		p1[0] = a1;
		p1[1] = b1;
		p1[2] = c1;
		p2[0] = a2;
		p2[1] = b2;
		p2[2] = c2;
		return pairing(p1, p2);
	}
	/// Convenience method for a pairing check for four pairs.
	function pairingProd4(
			G1Point a1, G2Point a2,
			G1Point b1, G2Point b2,
			G1Point c1, G2Point c2,
			G1Point d1, G2Point d2
	) internal returns (bool) {
		G1Point[] memory p1 = new G1Point[](4);
		G2Point[] memory p2 = new G2Point[](4);
		p1[0] = a1;
		p1[1] = b1;
		p1[2] = c1;
		p1[3] = d1;
		p2[0] = a2;
		p2[1] = b2;
		p2[2] = c2;
		p2[3] = d2;
		return pairing(p1, p2);
	}
}
