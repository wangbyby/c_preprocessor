#include "pp.hpp"
#include <iostream>

int main() {
    std::cout << "=== Testing Hex Number Conditions ===\n\n";
    
    // Test hex number in condition - should be true since 0x10 = 16 != 0
    std::string input = R"(#if 0x10
int hex_true = 1;
#else
int hex_false = 0;
#endif)";
    
    PreProcessor pp(input);
    std::string result = pp.expandMacros();
    
    std::cout << "Input:\n" << input << "\n";
    std::cout << "Output:\n" << result << "\n";
    
    if (result.find("hex_true") != std::string::npos) {
        std::cout << "✓ PASSED - 0x10 correctly evaluated as true (non-zero)\n";
    } else {
        std::cout << "✗ FAILED - 0x10 should evaluate as true\n";
    }
    
    return 0;
}