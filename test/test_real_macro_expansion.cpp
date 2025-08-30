#include "pp.hpp"
#include <iostream>
#include <string>

class RealMacroTester {
private:
    int testCount = 0;
    int passedTests = 0;

    std::string normalizeSpaces(const std::string& str) {
        std::string result;
        bool lastWasSpace = false;
        
        for (char c : str) {
            if (std::isspace(c)) {
                if (!lastWasSpace && !result.empty()) {
                    result += ' ';
                    lastWasSpace = true;
                }
            } else {
                result += c;
                lastWasSpace = false;
            }
        }
        
        // Trim trailing space
        if (!result.empty() && result.back() == ' ') {
            result.pop_back();
        }
        
        return result;
    }

public:
    void runTest(const std::string& testName, const std::string& input, const std::string& expected) {
        testCount++;
        std::cout << "\n=== Test " << testCount << ": " << testName << " ===\n";
        std::cout << "Input:\n" << input << "\n";
        
        try {
            PreProcessor pp(input);
            std::string rawResult = pp.expandMacros();
            std::string result = normalizeSpaces(rawResult);
            std::string normalizedExpected = normalizeSpaces(expected);
            
            std::cout << "Output:\n" << result << "\n";
            std::cout << "Expected:\n" << normalizedExpected << "\n";
            
            if (result == normalizedExpected) {
                std::cout << "✓ PASSED\n";
                passedTests++;
            } else {
                std::cout << "✗ FAILED\n";
            }
        } catch (const std::exception& e) {
            std::cout << "Error: " << e.what() << "\n";
            std::cout << "✗ FAILED (Exception)\n";
        }
    }
    
    void printSummary() {
        std::cout << "\n=== Test Summary ===\n";
        std::cout << "Total tests: " << testCount << "\n";
        std::cout << "Passed: " << passedTests << "\n";
        std::cout << "Failed: " << (testCount - passedTests) << "\n";
        
        if (passedTests == testCount) {
            std::cout << "🎉 All tests passed!\n";
        } else {
            std::cout << "❌ Some tests failed.\n";
        }
    }
};

int main() {
    RealMacroTester tester;
    
    // Test 1: Simple object macro
    tester.runTest(
        "Simple Object Macro",
        "#define PI 3.14159\nfloat radius = PI;",
        "float radius = 3.14159;"
    );
    
    // Test 2: Multiple object macros
    tester.runTest(
        "Multiple Object Macros",
        "#define WIDTH 800\n#define HEIGHT 600\nint w = WIDTH; int h = HEIGHT;",
        "int w = 800; int h = 600;"
    );
    
    // Test 3: Function macro with single parameter
    tester.runTest(
        "Function Macro Single Param",
        "#define SQUARE(x) ((x) * (x))\nint result = SQUARE(5);",
        "int result = ((5) * (5));"
    );
    
    // Test 4: Function macro with multiple parameters
    tester.runTest(
        "Function Macro Multiple Params",
        "#define MAX(a, b) ((a) > (b) ? (a) : (b))\nint max_val = MAX(10, 20);",
        "int max_val = ((10) > (20) ? (10) : (20));"
    );
    
    // Test 5: String macro
    tester.runTest(
        "String Macro",
        "#define GREETING \"Hello World\"\nprintf(GREETING);",
        "printf(\"Hello World\");"
    );
    
    // Test 6: Conditional compilation - true
    tester.runTest(
        "Conditional True",
        "#define DEBUG 1\n#if DEBUG\nint debug_var = 42;\n#endif",
        "int debug_var = 42;"
    );
    
    // Test 7: Conditional compilation - false with else
    tester.runTest(
        "Conditional False with Else",
        "#define DEBUG 0\n#if DEBUG\nint debug_var = 1;\n#else\nint release_var = 2;\n#endif",
        "int release_var = 2;"
    );
    
    // Test 8: Undef macro
    tester.runTest(
        "Undef Macro",
        "#define TEMP 123\nint x = TEMP;\n#undef TEMP\nint y = TEMP;",
        "int x = 123; int y = TEMP;"
    );
    
    // Test 9: Function macro with expressions
    tester.runTest(
        "Function Macro with Expressions",
        "#define ADD(x, y) ((x) + (y))\nint sum = ADD(a + 1, b * 2);",
        "int sum = ((a + 1) + (b * 2));"
    );
    
    // Test 10: Macro not expanded without parentheses
    tester.runTest(
        "Function Macro Without Parens",
        "#define FUNC(x) ((x) + 1)\nint ptr = FUNC;",
        "int ptr = FUNC;"
    );
    
    // Test 11: Complex expression
    tester.runTest(
        "Complex Expression",
        "#define CLAMP(val, min, max) ((val) < (min) ? (min) : (val))\nint result = CLAMP(x, 0, 100);",
        "int result = ((x) < (0) ? (0) : (x));"
    );
    
    // Test 12: Multiple macros in one expression
    tester.runTest(
        "Multiple Macros in Expression",
        "#define A 10\n#define B 20\nint sum = A + B * A;",
        "int sum = 10 + 20 * 10;"
    );
    
    tester.printSummary();
    return 0;
}