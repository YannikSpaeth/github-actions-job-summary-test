#include <gtest/gtest.h>
#include "utils.h"

// ============================================================
// Test suite: demo_utils_add
// ============================================================

TEST(demo_utils_add, PositiveNumbers) {
    EXPECT_EQ(add(3, 4), 7);
}

TEST(demo_utils_add, NegativeNumbers) {
    EXPECT_EQ(add(-2, -3), -5);
}

TEST(demo_utils_add, ZeroValues) {
    EXPECT_EQ(add(0, 0), 0);
}

// ============================================================
// Test suite: demo_utils_divide
// ============================================================

TEST(demo_utils_divide, NormalDivision) {
    EXPECT_DOUBLE_EQ(divide(10.0, 2.0), 5.0);
}

TEST(demo_utils_divide, DivisionByZero) {
    EXPECT_DOUBLE_EQ(divide(5.0, 0.0), 0.0);
}

// Intentional FAILURE: wrong expected value
TEST(demo_utils_divide, FaultyExpectation) {
    // 10/3 ≈ 3.333... but we expect 3.0 — this WILL fail
    EXPECT_DOUBLE_EQ(divide(10.0, 3.0), 3.0);
}

// ============================================================
// Test suite: demo_utils_is_positive
// ============================================================

TEST(demo_utils_is_positive, PositiveValue) {
    EXPECT_TRUE(is_number_positive(42));
}

TEST(demo_utils_is_positive, NegativeValue) {
    EXPECT_FALSE(is_number_positive(-1));
}

TEST(demo_utils_is_positive, ZeroIsNotPositive) {
    EXPECT_FALSE(is_number_positive(0));
}

// Intentional FAILURE: -5 is not positive
TEST(demo_utils_is_positive, FaultyZeroCheck) {
    // This WILL fail — -5 is not positive
    EXPECT_TRUE(is_number_positive(-5));
}
