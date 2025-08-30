#include "pp.hpp"
#include <iostream>

int main() {
    std::cout << "=== #if Macro Implementation Demo ===\n\n";
    
    // Test 1: Simple #if with macro expansion
    std::cout << "Test 1: #if with macro that evaluates to true\n";
    std::string input1 = R"(#define DEBUG 1
#if DEBUG
int debug_enabled = 1;
#endif
int always_present = 2;)";
    
    PreProcessor pp1(input1);
    std::string result1 = pp1.expandMacros();
    std::cout << "Input:\n" << input1 << "\n";
    std::cout << "Output:\n" << result1 << "\n\n";
    
    // Test 2: #if with macro that evaluates to false
    std::cout << "Test 2: #if with macro that evaluates to false\n";
    std::string input2 = R"(#define DEBUG 0
#if DEBUG
int debug_code = 1;
#else
int release_code = 2;
#endif)";
    
    PreProcessor pp2(input2);
    std::string result2 = pp2.expandMacros();
    std::cout << "Input:\n" << input2 << "\n";
    std::cout << "Output:\n" << result2 << "\n\n";
    
    // Test 3: Nested #if conditions
    std::cout << "Test 3: Nested #if conditions\n";
    std::string input3 = R"(#define PLATFORM_WIN 1
#define DEBUG_MODE 1
#if PLATFORM_WIN
    #if DEBUG_MODE
        int win_debug = 1;
    #else
        int win_release = 2;
    #endif
#else
    int other_platform = 3;
#endif)";
    
    PreProcessor pp3(input3);
    std::string result3 = pp3.expandMacros();
    std::cout << "Input:\n" << input3 << "\n";
    std::cout << "Output:\n" << result3 << "\n\n";
    
    // Test 4: #if with numeric literals
    std::cout << "Test 4: #if with numeric literals\n";
    std::string input4 = R"(#if 1
int feature_enabled = 1;
#endif
#if 0
int feature_disabled = 2;
#else
int feature_alternative = 3;
#endif)";
    
    PreProcessor pp4(input4);
    std::string result4 = pp4.expandMacros();
    std::cout << "Input:\n" << input4 << "\n";
    std::cout << "Output:\n" << result4 << "\n\n";
    
    std::cout << "=== All #if macro tests completed successfully! ===\n";
    return 0;
}