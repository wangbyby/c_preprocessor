#include "pp.hpp"
#include <iostream>
#include <sstream>

class SimplePreProcessorTester {
private:
    int testCount = 0;
    int passedTests = 0;

public:
    void runTest(const std::string& testName, const std::string& input, const std::string& expected) {
        testCount++;
        std::cout << "\n=== Test " << testCount << ": " << testName << " ===\n";
        std::cout << "Input:\n" << input << "\n";
        
        try {
            std::string result = processAndTokenize(input);
            std::cout << "Output:\n" << result << "\n";
            std::cout << "Expected:\n" << expected << "\n";
            
            if (result == expected) {
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

private:
    std::string processAndTokenize(const std::string& input) {
        PreProcessor pp(input);
        std::ostringstream output;
        
        // Process and tokenize, showing what remains after preprocessing
        while (true) {
            Token token = pp.next();
            if (token.kind == TokenKind::T_EOF) {
                break;
            }
            
            // Skip preprocessor directives and newlines
            if (token.kind == TokenKind::Hash || token.kind == TokenKind::Unknown) {
                continue;
            }
            
            // Get actual token text
            std::string tokenText = pp.getTokenText(token);
            output << tokenText << " ";
        }
        
        std::string result = output.str();
        // Trim trailing whitespace
        while (!result.empty() && std::isspace(result.back())) {
            result.pop_back();
        }
        
        return result;
    }
};

int main() {
    SimplePreProcessorTester tester;
    
    // Test 1: Basic tokenization without macros
    tester.runTest(
        "Basic Tokenization",
        "int x = 42;",
        "int x = 42 ;"
    );
    
    // Test 2: Tokenization with preprocessor directive (directive should be skipped)
    tester.runTest(
        "Skip Preprocessor Directive",
        "#define PI 3.14159\nint x = 42;",
        "int x = 42 ;"
    );
    
    // Test 3: Multiple directives
    tester.runTest(
        "Multiple Directives",
        "#define MAX_SIZE 100\n#define MIN_SIZE 10\nint array[50];",
        "int array [ 50 ] ;"
    );
    
    // Test 4: Function macro definition (should be skipped)
    tester.runTest(
        "Function Macro Definition",
        "#define SQUARE(x) ((x) * (x))\nint result = 25;",
        "int result = 25 ;"
    );
    
    // Test 5: Conditional compilation
    tester.runTest(
        "Conditional Compilation",
        "#if 1\nint enabled = 1;\n#endif\nint always = 2;",
        "int enabled = 1 ; int always = 2 ;"
    );
    
    // Test 6: Conditional with else
    tester.runTest(
        "Conditional with Else",
        "#if 0\nint disabled = 1;\n#else\nint enabled = 2;\n#endif",
        "int enabled = 2 ;"
    );
    
    // Test 7: Nested conditionals
    tester.runTest(
        "Nested Conditionals",
        "#if 1\n#if 1\nint nested = 42;\n#endif\n#endif",
        "int nested = 42 ;"
    );
    
    // Test 8: Undef test
    tester.runTest(
        "Undef Test",
        "#define TEMP 123\n#undef TEMP\nint x = 456;",
        "int x = 456 ;"
    );
    
    // Test 9: String literals
    tester.runTest(
        "String Literals",
        "#define MSG \"Hello\"\nprintf(\"World\");",
        "printf ( \"World\" ) ;"
    );
    
    // Test 10: Complex expression
    tester.runTest(
        "Complex Expression",
        "#define DEBUG 1\n#if DEBUG\nresult = (a + b) * c;\n#endif",
        "result = ( a + b ) * c ;"
    );
    
    tester.printSummary();
    return 0;
}