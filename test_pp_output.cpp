#include "pp.hpp"
#include <iostream>
#include <sstream>
#include <cassert>

class PreProcessorTester {
private:
    int testCount = 0;
    int passedTests = 0;

public:
    void runTest(const std::string& testName, const std::string& input, const std::string& expected) {
        testCount++;
        std::cout << "\n=== Test " << testCount << ": " << testName << " ===\n";
        std::cout << "Input:\n" << input << "\n";
        
        try {
            std::string result = processInput(input);
            std::cout << "Output:\n" << result << "\n";
            std::cout << "Expected:\n" << expected << "\n";
            
            if (result == expected) {
                std::cout << "✓ PASSED\n";
                passedTests++;
            } else {
                std::cout << "✗ FAILED\n";
                std::cout << "Difference found!\n";
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
    std::string processInput(const std::string& input) {
        PreProcessor pp(input);
        
        // First, process all preprocessor directives
        pp.process();
        
        // Now create a new preprocessor with the processed buffer to tokenize the result
        PreProcessor pp2(pp.getBuffer());
        std::ostringstream output;
        
        // Process all tokens and reconstruct the output
        while (true) {
            Token token = pp2.next();
            if (token.kind == TokenKind::T_EOF) {
                break;
            }
            
            // Skip preprocessor directives in output
            if (token.kind == TokenKind::Hash) {
                skipDirectiveLine(pp2);
                continue;
            }
            
            // Skip newlines for cleaner output comparison
            if (token.kind == TokenKind::Unknown) {
                continue;
            }
            
            // Add the actual token text to output
            std::string tokenText = pp2.getTokenText(token);
            output << tokenText;
            
            // Add space between tokens for readability (except punctuation)
            if (token.kind == TokenKind::Ident || token.kind == TokenKind::Number || 
                token.kind == TokenKind::StringLiteral) {
                output << " ";
            }
        }
        
        std::string result = output.str();
        // Trim trailing whitespace
        while (!result.empty() && std::isspace(result.back())) {
            result.pop_back();
        }
        
        return result;
    }
    
    void skipDirectiveLine(PreProcessor& pp) {
        // Skip tokens until we hit EOF or newline
        while (true) {
            Token token = pp.next();
            if (token.kind == TokenKind::T_EOF || token.kind == TokenKind::Unknown) {
                break;
            }
        }
    }
};

int main() {
    PreProcessorTester tester;
    
    // Test 1: Simple object macro
    tester.runTest(
        "Simple Object Macro",
        "#define PI 3.14159\nPI",
        "NUMBER"
    );
    
    // Test 2: Multiple object macros
    tester.runTest(
        "Multiple Object Macros", 
        "#define MAX_SIZE 100\n#define MIN_SIZE 10\nMAX_SIZE MIN_SIZE",
        "NUMBER NUMBER"
    );
    
    // Test 3: Function macro
    tester.runTest(
        "Function Macro",
        "#define SQUARE(x) ((x) * (x))\nSQUARE(5)",
        "( ( NUMBER ) * ( NUMBER ) )"
    );
    
    // Test 4: Macro with string
    tester.runTest(
        "Macro with String",
        "#define GREETING \"Hello\"\nGREETING",
        "STRING"
    );
    
    // Test 5: Conditional compilation - true condition
    tester.runTest(
        "Conditional True",
        "#define DEBUG 1\n#if DEBUG\nint x = 42;\n#endif",
        "IDENT IDENT = NUMBER ;"
    );
    
    // Test 6: Conditional compilation - false condition  
    tester.runTest(
        "Conditional False",
        "#define DEBUG 0\n#if DEBUG\nint x = 42;\n#else\nint y = 24;\n#endif",
        "IDENT IDENT = NUMBER ;"
    );
    
    // Test 7: Undef macro
    tester.runTest(
        "Undef Macro",
        "#define TEMP 123\n#undef TEMP\nTEMP",
        "IDENT"
    );
    
    // Test 8: Nested conditionals
    tester.runTest(
        "Nested Conditionals",
        "#define PLATFORM 1\n#define DEBUG 1\n#if PLATFORM\n#if DEBUG\nint debug_var;\n#endif\n#endif",
        "IDENT IDENT ;"
    );
    
    // Test 9: Function macro with multiple parameters
    tester.runTest(
        "Function Macro Multiple Params",
        "#define ADD(a, b) ((a) + (b))\nADD(10, 20)",
        "( ( NUMBER ) + ( NUMBER ) )"
    );
    
    // Test 10: Complex macro replacement
    tester.runTest(
        "Complex Macro",
        "#define MAX(a,b) ((a)>(b)?(a):(b))\nint result = MAX(x, y);",
        "IDENT IDENT = ( ( IDENT ) > ( IDENT ) ? ( IDENT ) : ( IDENT ) ) ;"
    );
    
    tester.printSummary();
    return 0;
}