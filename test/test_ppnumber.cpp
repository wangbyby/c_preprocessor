#include "pp.hpp"
#include <iostream>
#include <vector>

class PPNumberTester {
private:
  int testCount = 0;
  int passedTests = 0;

public:
  void testPPNumber(const std::string &input,
                    const std::string &expectedToken) {
    testCount++;
    std::cout << "\n=== PPNumber Test " << testCount << " ===\n";
    std::cout << "Input: " << input << "\n";

    try {
      PreProcessor pp(input);
      Token token = pp.next();

      if (token.kind == TokenKind::PPNumber) {
        std::string actualToken = pp.getTokenText(token);
        std::cout << "Parsed PPNumber: " << actualToken << "\n";
        std::cout << "Expected: " << expectedToken << "\n";

        if (actualToken == expectedToken) {
          std::cout << "✓ PASSED\n";
          passedTests++;
        } else {
          std::cout << "✗ FAILED - Token mismatch\n";
        }
      } else {
        std::cout << "✗ FAILED - Not recognized as PPNumber\n";
      }
    } catch (const std::exception &e) {
      std::cout << "✗ FAILED - Exception: " << e.what() << "\n";
    }
  }

  void testTokenSequence(const std::string &input,
                         const std::vector<std::string> &expectedTokens) {
    testCount++;
    std::cout << "\n=== Token Sequence Test " << testCount << " ===\n";
    std::cout << "Input: " << input << "\n";

    try {
      PreProcessor pp(input);
      std::vector<std::string> actualTokens;

      while (true) {
        Token token = pp.next();
        if (token.kind == TokenKind::T_EOF) {
          break;
        }
        if (token.kind != TokenKind::Unknown) { // Skip newlines
          actualTokens.push_back(pp.getTokenText(token));
        }
      }

      std::cout << "Parsed tokens: ";
      for (const auto &token : actualTokens) {
        std::cout << "'" << token << "' ";
      }
      std::cout << "\n";

      std::cout << "Expected tokens: ";
      for (const auto &token : expectedTokens) {
        std::cout << "'" << token << "' ";
      }
      std::cout << "\n";

      if (actualTokens == expectedTokens) {
        std::cout << "✓ PASSED\n";
        passedTests++;
      } else {
        std::cout << "✗ FAILED - Token sequence mismatch\n";
      }
    } catch (const std::exception &e) {
      std::cout << "✗ FAILED - Exception: " << e.what() << "\n";
    }
  }

  void printSummary() {
    std::cout << "\n=== PPNumber Test Summary ===\n";
    std::cout << "Total tests: " << testCount << "\n";
    std::cout << "Passed: " << passedTests << "\n";
    std::cout << "Failed: " << (testCount - passedTests) << "\n";

    if (passedTests == testCount) {
      std::cout << "🎉 All PPNumber tests passed!\n";
    } else {
      std::cout << "❌ Some PPNumber tests failed.\n";
    }
  }
};

int main() {
  std::cout << "=== PPNumber Parser Test Suite ===\n";

  PPNumberTester tester;

  // Test basic integers
  tester.testPPNumber("123", "123");
  tester.testPPNumber("0", "0");
  tester.testPPNumber("999", "999");

  // Test decimal numbers
  tester.testPPNumber("3.14159", "3.14159");
  tester.testPPNumber(".5", ".5");
  tester.testPPNumber("0.0", "0.0");
  tester.testPPNumber("123.456", "123.456");

  // Test scientific notation
  tester.testPPNumber("1e10", "1e10");
  tester.testPPNumber("2.5e-3", "2.5e-3");
  tester.testPPNumber("1E+5", "1E+5");
  tester.testPPNumber("3.14e0", "3.14e0");

  // Test hexadecimal numbers
  tester.testPPNumber("0x123", "0x123");
  tester.testPPNumber("0xFF", "0xFF");
  tester.testPPNumber("0xABCDEF", "0xABCDEF");

  // Test hexadecimal with p exponent
  tester.testPPNumber("0x1.5p+3", "0x1.5p+3");
  tester.testPPNumber("0xA.Bp-2", "0xA.Bp-2");

  // Test numbers with suffixes
  tester.testPPNumber("123L", "123L");
  tester.testPPNumber("456UL", "456UL");
  tester.testPPNumber("3.14f", "3.14f");
  tester.testPPNumber("2.5F", "2.5F");
  tester.testPPNumber("1.0L", "1.0L");

  // Test octal numbers
  tester.testPPNumber("0123", "0123");
  tester.testPPNumber("0777", "0777");

  // Test token sequences with numbers
  tester.testTokenSequence("int x = 42;", {"int", "x", "=", "42", ";"});
  tester.testTokenSequence("float pi = 3.14159;",
                           {"float", "pi", "=", "3.14159", ";"});
  tester.testTokenSequence("double e = 2.71828e0;",
                           {"double", "e", "=", "2.71828e0", ";"});
  tester.testTokenSequence("unsigned long val = 123UL;",
                           {"unsigned", "long", "val", "=", "123UL", ";"});
  tester.testTokenSequence("hex = 0xFF + 0x10;",
                           {"hex", "=", "0xFF", "+", "0x10", ";"});

  // Test edge cases
  tester.testTokenSequence(
      "a.b", {"a", ".", "b"}); // Should be identifier, dot, identifier
  tester.testTokenSequence(".5f", {".5f"});   // Should be one ppnumber
  tester.testTokenSequence("1.e5", {"1.e5"}); // Should be one ppnumber

  tester.printSummary();
  return 0;
}