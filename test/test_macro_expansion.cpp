#include "pp.hpp"
#include <iostream>
#include <string>

class MacroExpansionTester {
private:
  int testCount = 0;
  int passedTests = 0;

public:
  void runTest(const std::string &testName, const std::string &input,
               const std::string &expected) {
    testCount++;
    std::cout << "\n=== Test " << testCount << ": " << testName << " ===\n";
    std::cout << "Input:\n" << input << "\n";

    try {
      PreProcessor pp(input);
      std::string result = pp.expandMacros();

      std::cout << "Output:\n" << result << "\n";
      std::cout << "Expected:\n" << expected << "\n";

      if (result == expected) {
        std::cout << "✓ PASSED\n";
        passedTests++;
      } else {
        std::cout << "✗ FAILED\n";
        std::cout << "Difference found!\n";
      }
    } catch (const std::exception &e) {
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
  MacroExpansionTester tester;

  // Test 1: Simple object macro
  tester.runTest("Simple Object Macro",
                 "#define PI 3.14159\nfloat radius = PI;",
                 "\nfloat radius = 3.14159;");

  // Test 2: Multiple object macros
  tester.runTest("Multiple Object Macros",
                 "#define MAX_SIZE 100\n#define MIN_SIZE 10\nint "
                 "array[MAX_SIZE];\nint min = MIN_SIZE;",
                 "\n\nint array[100];\nint min = 10;");

  // Test 3: Function macro with single parameter
  tester.runTest("Function Macro Single Param",
                 "#define SQUARE(x) ((x) * (x))\nint result = SQUARE(5);",
                 "\nint result = ((5) * (5));");

  // Test 4: Function macro with multiple parameters
  tester.runTest(
      "Function Macro Multiple Params",
      "#define MAX(a, b) ((a) > (b) ? (a) : (b))\nint max_val = MAX(10, 20);",
      "\nint max_val = ((10) > (20) ? (10) : (20));");

  // Test 5: Function macro with expressions as arguments
  tester.runTest("Function Macro with Expressions",
                 "#define ADD(x, y) ((x) + (y))\nint sum = ADD(a + 1, b * 2);",
                 "\nint sum = ((a + 1) + (b * 2));");

  // Test 6: Macro with string replacement
  tester.runTest("String Macro",
                 "#define GREETING \"Hello World\"\nprintf(GREETING);",
                 "\nprintf(\"Hello World\");");

  // Test 7: Conditional compilation with macro expansion
  tester.runTest("Conditional with Macro",
                 "#define DEBUG 1\n#if DEBUG\n#define LOG_LEVEL 3\n#endif\nint "
                 "level = LOG_LEVEL;",
                 "\n\n\nint level = 3;");

  // Test 8: Undef and redefine
  tester.runTest("Undef and Redefine",
                 "#define TEMP 42\nint x = TEMP;\n#undef TEMP\n#define TEMP "
                 "84\nint y = TEMP;",
                 "\nint x = 42;\n\nint y = 84;");

  // Test 9: Nested function macro calls
  tester.runTest("Nested Function Macros",
                 "#define DOUBLE(x) ((x) * 2)\n#define TRIPLE(x) ((x) * "
                 "3)\nint result = DOUBLE(TRIPLE(5));",
                 "\n\nint result = ((TRIPLE(5)) * 2);");

  // Test 10: Complex macro with multiple operations
  tester.runTest(
      "Complex Macro",
      "#define CLAMP(val, min, max) ((val) < (min) ? (min) : ((val) > (max) ? "
      "(max) : (val)))\nint clamped = CLAMP(value, 0, 100);",
      "\nint clamped = ((value) < (0) ? (0) : ((value) > (100) ? (100) : "
      "(value)));");

  // Test 11: Macro not used (should remain as identifier)
  tester.runTest("Unused Macro",
                 "#define UNUSED_MACRO 42\nint x = some_other_var;",
                 "\nint x = some_other_var;");

  // Test 12: Function-like macro without parentheses (should not expand)
  tester.runTest("Function Macro Without Parens",
                 "#define FUNC(x) ((x) + 1)\nint ptr = FUNC;",
                 "\nint ptr = FUNC;");

  // Test 13: Conditional false branch
  tester.runTest("Conditional False",
                 "#define DEBUG 0\n#if DEBUG\nint debug_var = 1;\n#else\nint "
                 "release_var = 2;\n#endif",
                 "\n\nint release_var = 2;\n");

  // Test 14: Multiple macros in one line
  tester.runTest("Multiple Macros in Line",
                 "#define A 10\n#define B 20\nint sum = A + B;",
                 "\n\nint sum = 10 + 20;");

  // Test 15: Macro with parentheses in replacement
  tester.runTest(
      "Macro with Parentheses",
      "#define SAFE_ADD(a, b) ((a) + (b))\nint result = SAFE_ADD(x, y) * 2;",
      "\nint result = ((x) + (y)) * 2;");

  tester.printSummary();
  return 0;
}