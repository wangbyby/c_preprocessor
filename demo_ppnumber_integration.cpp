#include "pp.hpp"
#include <iostream>

int main() {
    std::cout << "=== PPNumber Integration with Preprocessor Demo ===\n\n";
    
    // Test 1: PPNumbers in macro definitions and expansions
    std::cout << "Test 1: PPNumbers in macro definitions\n";
    std::string input1 = R"(#define PI 3.14159
#define BUFFER_SIZE 1024
#define SCIENTIFIC 2.5e-3
#define HEX_VALUE 0xFF
#define FLOAT_SUFFIX 1.5f
float pi = PI;
int buffer[BUFFER_SIZE];
double sci = SCIENTIFIC;
unsigned hex = HEX_VALUE;
float f = FLOAT_SUFFIX;)";
    
    PreProcessor pp1(input1);
    std::string result1 = pp1.expandMacros();
    std::cout << "Input:\n" << input1 << "\n";
    std::cout << "Output:\n" << result1 << "\n\n";
    
    // Test 2: PPNumbers in conditional compilation
    std::cout << "Test 2: PPNumbers in conditional compilation\n";
    std::string input2 = R"(#define VERSION 2
#if VERSION
    int version_2_feature = 42;
#endif
#if 0x10
    int hex_condition = 16;
#endif
#if 3.14
    int float_condition = 1;
#endif)";
    
    PreProcessor pp2(input2);
    std::string result2 = pp2.expandMacros();
    std::cout << "Input:\n" << input2 << "\n";
    std::cout << "Output:\n" << result2 << "\n\n";
    
    // Test 3: Complex PPNumbers with function macros
    std::cout << "Test 3: Complex PPNumbers with function macros\n";
    std::string input3 = R"(#define MULTIPLY(a, b) ((a) * (b))
#define SCIENTIFIC_CALC(x) ((x) * 1e6)
#define HEX_SHIFT(val) ((val) << 0x4)
double result1 = MULTIPLY(3.14159, 2.0);
double result2 = SCIENTIFIC_CALC(2.5e-3);
int result3 = HEX_SHIFT(0xFF);)";
    
    PreProcessor pp3(input3);
    std::string result3 = pp3.expandMacros();
    std::cout << "Input:\n" << input3 << "\n";
    std::cout << "Output:\n" << result3 << "\n\n";
    
    // Test 4: Edge cases with PPNumbers
    std::cout << "Test 4: Edge cases with PPNumbers\n";
    std::string input4 = R"(#define DOT_FIVE .5
#define LONG_SUFFIX 123L
#define UNSIGNED_LONG 456UL
#define HEX_FLOAT 0x1.5p+3
float dot = DOT_FIVE;
long lng = LONG_SUFFIX;
unsigned long ul = UNSIGNED_LONG;
double hf = HEX_FLOAT;)";
    
    PreProcessor pp4(input4);
    std::string result4 = pp4.expandMacros();
    std::cout << "Input:\n" << input4 << "\n";
    std::cout << "Output:\n" << result4 << "\n\n";
    
    // Test 5: Tokenization demonstration
    std::cout << "Test 5: Tokenization of various PPNumbers\n";
    std::string input5 = "123 3.14 .5 1e10 0xFF 0x1.5p+3 123L 456UL 2.5f";
    PreProcessor pp5(input5);
    
    std::cout << "Input: " << input5 << "\n";
    std::cout << "Tokens: ";
    
    while (true) {
        Token token = pp5.next();
        if (token.kind == TokenKind::T_EOF) {
            break;
        }
        if (token.kind != TokenKind::Unknown) {
            std::string tokenText = pp5.getTokenText(token);
            std::string kindName = (token.kind == TokenKind::PPNumber) ? "PPNumber" : "Other";
            std::cout << "[" << tokenText << ":" << kindName << "] ";
        }
    }
    std::cout << "\n\n";
    
    std::cout << "=== PPNumber integration demonstration completed! ===\n";
    return 0;
}