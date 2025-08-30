#include "pp.hpp"
#include <iostream>

int main() {
    std::cout << "=== Simple Macro Expansion Test ===\n\n";
    
    // Test 1: Simple object macro
    std::cout << "Test 1: Simple Object Macro\n";
    std::string input1 = "#define PI 3.14159\nfloat x = PI;";
    std::cout << "Input: " << input1 << "\n";
    
    try {
        PreProcessor pp1(input1);
        std::string result1 = pp1.expandMacros();
        std::cout << "Output: " << result1 << "\n\n";
    } catch (const std::exception& e) {
        std::cout << "Error: " << e.what() << "\n\n";
    }
    
    // Test 2: Function macro
    std::cout << "Test 2: Function Macro\n";
    std::string input2 = "#define SQUARE(x) ((x) * (x))\nint y = SQUARE(5);";
    std::cout << "Input: " << input2 << "\n";
    
    try {
        PreProcessor pp2(input2);
        std::string result2 = pp2.expandMacros();
        std::cout << "Output: " << result2 << "\n\n";
    } catch (const std::exception& e) {
        std::cout << "Error: " << e.what() << "\n\n";
    }
    
    // Test 3: Conditional compilation
    std::cout << "Test 3: Conditional Compilation\n";
    std::string input3 = "#define DEBUG 1\n#if DEBUG\nint debug_mode = 1;\n#endif";
    std::cout << "Input: " << input3 << "\n";
    
    try {
        PreProcessor pp3(input3);
        std::string result3 = pp3.expandMacros();
        std::cout << "Output: " << result3 << "\n\n";
    } catch (const std::exception& e) {
        std::cout << "Error: " << e.what() << "\n\n";
    }
    
    return 0;
}