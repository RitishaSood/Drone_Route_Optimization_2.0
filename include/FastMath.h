#pragma once
#include <cmath>

class FastMath {
private:
    static constexpr int LUT_SIZE = 10000;
    static constexpr double MAX_VAL = 50.0; // Expanded to handle high gamma*d values
    double exp_lut[LUT_SIZE];

    FastMath() {
        for (int i = 0; i < LUT_SIZE; ++i) {
            double x = (double)i / LUT_SIZE * MAX_VAL;
            exp_lut[i] = std::exp(-x);
        }
    }

public:
    static FastMath& get() {
        static FastMath instance;
        return instance;
    }

    inline double exp_neg(double x) const {
        if (x < 0.0) return std::exp(-x); 
        if (x >= MAX_VAL) return 0.0;
        int idx = static_cast<int>((x / MAX_VAL) * LUT_SIZE);
        return exp_lut[idx];
    }
};