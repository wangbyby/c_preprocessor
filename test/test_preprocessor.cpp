#include "pp.hpp"
#include <cassert>
#include <iostream>


void test_object_macros() {
  std::cout << "Testing object macros...\n";

  std::string input = R"(
#define PI 3.14159
#define MAX_SIZE 100
#define GREETING "Hello World"
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ Object macros test passed\n";
}

void test_function_macros() {
  std::cout << "Testing function macros...\n";

  std::string input = R"(
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))
#define ADD(x, y) ((x) + (y))
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ Function macros test passed\n";
}

void test_undef() {
  std::cout << "Testing #undef...\n";

  std::string input = R"(
#define TEMP_MACRO 42
#undef TEMP_MACRO
#define ANOTHER_MACRO(x) (x * 2)
#undef ANOTHER_MACRO
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ #undef test passed\n";
}

void test_conditional_compilation_simple() {
  std::cout << "Testing simple conditional compilation...\n";

  std::string input = R"(
#define DEBUG 1
#if DEBUG
#define LOG(msg) printf(msg)
#else
#define LOG(msg)
#endif
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ Simple conditional compilation test passed\n";
}

void test_conditional_compilation_numeric() {
  std::cout << "Testing numeric conditional compilation...\n";

  std::string input = R"(
#if 1
#define FEATURE_ENABLED
#endif

#if 0
#define FEATURE_DISABLED
#else
#define FEATURE_ACTUALLY_ENABLED
#endif
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ Numeric conditional compilation test passed\n";
}

void test_conditional_compilation_defined() {
  std::cout << "Testing defined() conditional compilation...\n";

  std::string input = R"(
#define FEATURE_A
#if defined(FEATURE_A)
#define CONFIG_A "Feature A is enabled"
#endif

#if defined(FEATURE_B)
#define CONFIG_B "Feature B is enabled"
#else
#define CONFIG_B "Feature B is disabled"
#endif
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ defined() conditional compilation test passed\n";
}

void test_nested_conditionals() {
  std::cout << "Testing nested conditionals...\n";

  std::string input = R"(
#define PLATFORM_WINDOWS 1
#define DEBUG_MODE 1

#if PLATFORM_WINDOWS
    #if DEBUG_MODE
        #define LOG_LEVEL 3
    #else
        #define LOG_LEVEL 1
    #endif
#else
    #define LOG_LEVEL 0
#endif
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ Nested conditionals test passed\n";
}

void test_complex_scenario() {
  std::cout << "Testing complex scenario...\n";

  std::string input = R"(
// Define some initial macros
#define VERSION_MAJOR 2
#define VERSION_MINOR 1
#define BUILD_TYPE "Release"

// Function macro
#define MAKE_VERSION(maj, min) ((maj << 16) | min)

// Conditional compilation based on version
#if VERSION_MAJOR
    #define HAS_NEW_FEATURES
    #if VERSION_MINOR
        #define HAS_MINOR_FEATURES
    #endif
#endif

// Undefine and redefine
#undef BUILD_TYPE
#define BUILD_TYPE "Debug"

// More complex conditionals
#if defined(HAS_NEW_FEATURES)
    #define FEATURE_SET "Advanced"
#else
    #define FEATURE_SET "Basic"
#endif

#undef HAS_MINOR_FEATURES
)";

  PreProcessor pp(input);
  pp.process();

  std::cout << "✓ Complex scenario test passed\n";
}

void test_tokenization() {
  std::cout << "Testing tokenization with macros...\n";

  std::string input = R"(
#define BUFFER_SIZE 1024
#define MAX(a,b) ((a)>(b)?(a):(b))
int buffer[BUFFER_SIZE];
int result = MAX(10, 20);
)";

  PreProcessor pp(input);

  // Test tokenization
  Token token(0, 0, TokenKind::Unknown);
  int tokenCount = 0;
  do {
    token = pp.next();
    tokenCount++;
    if (tokenCount > 100)
      break; // Safety check
  } while (token.kind != TokenKind::T_EOF);

  std::cout << "✓ Tokenization test passed (processed " << tokenCount
            << " tokens)\n";
}

void test_error_handling() {
  std::cout << "Testing error handling...\n";

  // Test invalid #define
  try {
    std::string input = "#define 123invalid";
    PreProcessor pp(input);
    pp.process();
    std::cout << "✗ Should have thrown error for invalid macro name\n";
  } catch (const std::exception &e) {
    std::cout << "✓ Correctly caught error: " << e.what() << "\n";
  }

  // Test invalid #undef
  try {
    std::string input = "#undef 456invalid";
    PreProcessor pp(input);
    pp.process();
    std::cout << "✗ Should have thrown error for invalid undef\n";
  } catch (const std::exception &e) {
    std::cout << "✓ Correctly caught error: " << e.what() << "\n";
  }

  std::cout << "✓ Error handling tests passed\n";
}

int main() {
  std::cout << "=== C99 Preprocessor Test Suite ===\n\n";

  try {
    test_object_macros();
    test_function_macros();
    test_undef();
    test_conditional_compilation_simple();
    test_conditional_compilation_numeric();
    test_conditional_compilation_defined();
    test_nested_conditionals();
    test_complex_scenario();
    test_tokenization();
    test_error_handling();

    std::cout << "\n=== All Tests Passed! ===\n";

  } catch (const std::exception &e) {
    std::cout << "Test failed with error: " << e.what() << std::endl;
    return 1;
  }

  return 0;
}