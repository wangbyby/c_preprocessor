#include "pp.hpp"
#include <iostream>
#include <sstream>

class WorkingPreProcessorTester {
private:
  int testCount = 0;
  int passedTests = 0;

public:
  void runDirectiveTest(const std::string &testName, const std::string &input,
                        bool shouldSucceed = true) {
    testCount++;
    std::cout << "\n=== Test " << testCount << ": " << testName << " ===\n";
    std::cout << "Input:\n" << input << "\n";

    try {
      PreProcessor pp(input);
      pp.process(); // This processes all directives

      if (shouldSucceed) {
        std::cout << "✓ PASSED - Directives processed successfully\n";
        passedTests++;
      } else {
        std::cout << "✗ FAILED - Expected exception but none was thrown\n";
      }
    } catch (const std::exception &e) {
      if (!shouldSucceed) {
        std::cout << "✓ PASSED - Expected exception: " << e.what() << "\n";
        passedTests++;
      } else {
        std::cout << "✗ FAILED - Unexpected exception: " << e.what() << "\n";
      }
    }
  }

  void runTokenizationTest(const std::string &testName,
                           const std::string &input,
                           const std::string &expected) {
    testCount++;
    std::cout << "\n=== Test " << testCount << ": " << testName << " ===\n";
    std::cout << "Input:\n" << input << "\n";

    try {
      std::string result = tokenizeInput(input);
      std::cout << "Output:\n" << result << "\n";
      std::cout << "Expected:\n" << expected << "\n";

      if (result == expected) {
        std::cout << "✓ PASSED\n";
        passedTests++;
      } else {
        std::cout << "✗ FAILED\n";
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

private:
  std::string tokenizeInput(const std::string &input) {
    PreProcessor pp(input);
    std::ostringstream output;

    // Just tokenize without processing directives
    while (true) {
      Token token = pp.next();
      if (token.kind == TokenKind::T_EOF) {
        break;
      }

      // Skip newlines
      if (token.kind == TokenKind::Unknown) {
        continue;
      }

      // Get token text and add to output
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
  WorkingPreProcessorTester tester;

  // Test directive processing (these should succeed)
  tester.runDirectiveTest("Simple Define", "#define PI 3.14159\n", true);

  tester.runDirectiveTest("Function Macro",
                          "#define MAX(a, b) ((a) > (b) ? (a) : (b))\n", true);

  tester.runDirectiveTest("Undef Macro", "#define TEMP 123\n#undef TEMP\n",
                          true);

  tester.runDirectiveTest("Conditional True", "#if 1\n#endif\n", true);

  tester.runDirectiveTest("Conditional False with Else",
                          "#if 0\n#else\n#endif\n", true);

  tester.runDirectiveTest("Nested Conditionals",
                          "#if 1\n#if 1\n#endif\n#endif\n", true);

  // Test error cases (these should fail)
  tester.runDirectiveTest("Invalid Define - No Name", "#define\n", false);

  tester.runDirectiveTest("Invalid Undef - No Name", "#undef\n", false);

  // Test tokenization (without preprocessing)
  tester.runTokenizationTest("Basic Tokenization", "int x = 42;",
                             "int x = 42 ;");

  tester.runTokenizationTest("Function Call", "printf(\"Hello World\");",
                             "printf ( \"Hello World\" ) ;");

  tester.runTokenizationTest("Arithmetic Expression", "result = (a + b) * c;",
                             "result = ( a + b ) * c ;");

  tester.runTokenizationTest("Preprocessor Directive Tokens",
                             "#define MAX_SIZE 100", "# define MAX_SIZE 100");

  tester.runTokenizationTest("Function Macro Tokens",
                             "#define SQUARE(x) ((x) * (x))",
                             "# define SQUARE ( x ) ( ( x ) * ( x ) )");

  tester.runTokenizationTest("Conditional Tokens", "#if DEBUG\nint x;\n#endif",
                             "# if DEBUG int x ; # endif");

  tester.printSummary();
  return 0;
}