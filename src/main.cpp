#include <iostream>
#include "utils.h"

int main() {
    
    std::cout << "=== demo_app ===" << std::endl;

    int sum = add(3, 4);
    std::cout << "add(3, 4) = " << sum << std::endl;

    double result = divide(10.0, 3.0);
    std::cout << "divide(10.0, 3.0) = " << result << std::endl;

    double bad = divide(5.0, 0.0);
    std::cout << "divide(5.0, 0.0) = " << bad << std::endl;

    std::cout << "is_number_positive(42) = " << std::boolalpha << is_number_positive(42) << std::endl;
    std::cout << "is_number_positive(-1) = " << std::boolalpha << is_number_positive(-1) << std::endl;

    std::cout << "=== done ===" << std::endl;
    return 0;
}
