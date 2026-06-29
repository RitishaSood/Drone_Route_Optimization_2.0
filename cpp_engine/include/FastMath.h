#pragma once

#include <cmath>

class FastMath
{
private:

    static constexpr int LUT_SIZE = 10000;
    static constexpr double MAX_EXP = 50.0;

    double exp_lut[LUT_SIZE];

    FastMath()
    {
        for(int i = 0; i < LUT_SIZE; ++i)
        {
            double x =
                (static_cast<double>(i) /
                 static_cast<double>(LUT_SIZE))
                * MAX_EXP;

            exp_lut[i] =
                std::exp(-x);
        }
    }

public:

    static FastMath& get()
    {
        static FastMath instance;
        return instance;
    }

    inline double exp_neg(double x) const
    {
        if(x < 0.0)
        {
            return std::exp(-x);
        }

        if(x < 0.05)
        {
            return std::exp(-x);
        }

        if(x >= MAX_EXP)
        {
            return 0.0;
        }

        int idx =
            static_cast<int>(
                (x / MAX_EXP) *
                LUT_SIZE);

        return exp_lut[idx];
    }

    inline double square(double x) const
    {
        return x * x;
    }

    inline double cube(double x) const
    {
        return x * x * x;
    }

    inline double distanceSq3D(
        double x1,
        double y1,
        double z1,
        double x2,
        double y2,
        double z2) const
    {
        double dx = x1 - x2;
        double dy = y1 - y2;
        double dz = z1 - z2;

        return dx * dx +
               dy * dy +
               dz * dz;
    }

    inline double kmToMeters(double km) const
    {
        return km * 1000.0;
    }

    inline double zUnitsToMeters(double z) const
    {
        return z * 100.0;
    }
};