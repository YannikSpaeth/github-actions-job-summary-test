#include "utils.h"
#include <iostream>

int add(int a, int b) {
    return a + b;
}

double divide(double a, double b) {
    if (b == 0.0) {
        std::cerr << "[warn] divide: division by zero, returning 0.0" << std::endl;
        return 0.0;
    }
    return a / b;
}

bool is_number_positive(int value) {
    return value > 0;
}
