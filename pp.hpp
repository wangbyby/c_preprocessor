#pragma once

#include <cassert>
#include <cctype>
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// TokenKind: Represents the type of tokens in the preprocessor
enum class TokenKind {
  T_EOF = -1,
  Unknown = 0,

  Ident,

  Include, // #include
  Define,  // #define
  Undef,   // #undef
  If,      // if
  Else,    // else
  IfDef,   // #ifdef
  IfNDef,  // #ifndef
  Endif,   // #endif

  // literals
  PPNumber,
  CharLiteral,
  StringLiteral,

  // Punctuators
  L_Bracket,           // [
  R_Bracket,           // ]
  L_Paren,             // (
  R_Paren,             // )
  L_Brace,             // {
  R_Brace,             // }
  Dot,                 // .
  Arrow,               // ->
  PlusPlus,            // ++
  MinusMinus,          // --
  Ampersand,           // &
  Star,                // *
  Plus,                // +
  Minus,               // -
  Tilde,               // ~
  Not,                 // !
  Slash,               // /
  Percent,             // %
  LessLess,            // <<
  GreaterGreater,      // >>
  Less,                // <
  Greater,             // >
  LessEqual,           // <=
  GreaterEqual,        // >=
  EqualEqual,          // ==
  ExclamationEqual,    // !=
  XOR,                 // ^
  BitOr,               // |
  LogicAnd,            // &&
  LogicOr,             // ||
  Question,            // ?
  Colon,               // :
  Semicolon,           // ;
  Ellipsis,            // ...
  Assign,              // =
  MulAssign,           // *=
  DivAssign,           // /=
  ModAssign,           // %=
  AddAssign,           // +=
  MinusEqual,          // -=
  LessLessEqual,       // <<=
  GreaterGreaterEqual, // >>=
  BitAndEqual,         // &=
  XorAssign,           // ^=
  OrAssign,            // |=
  Comma,               // ,
  Hash,                // #
  HashHash             // ##

};

// Token: Represents a single token
struct Token {
  unsigned begin;
  unsigned len;
  TokenKind kind;

  Token(unsigned b, unsigned l, TokenKind k) : begin(b), len(l), kind(k) {}
};

struct LinColQuery {
  std::vector<unsigned> lineoffset;

  LinColQuery() {
    lineoffset.push_back(0); // Line 1 starts at offset 0
  }

  void addLine(unsigned lineStartOffset, bool isInclude = false) {
    if (isInclude)
      return;

    lineoffset.push_back(lineStartOffset);
  }

  std::pair<unsigned, unsigned> getLineCol(unsigned offset) const {
    unsigned line = 1;
    unsigned col = offset + 1; // Columns are 1-based

    auto it = std::lower_bound(lineoffset.begin(), lineoffset.end(), offset);
    if (it == lineoffset.end()) {
      line = lineoffset.size();
      col = offset - lineoffset.back() + 1;
    } else if (it == lineoffset.begin()) {
      line = 1;
      col = offset + 1;
    } else {
      line = std::distance(lineoffset.begin(), it);
      col = offset - *(it) + 1;
    }

    return {line, col};
  }
};

// PreProcessor: The main class for the preprocessor
class PreProcessor {
private:
  std::string buffer;
  unsigned cursor = 0;
  std::map<std::string, std::string> macros; // Stores object macros
  std::map<std::string, std::vector<std::string>>
      functionMacros; // Stores function macros
  std::map<std::string, std::string>
      functionMacroReplacements; // Stores function macro replacement text

  std::vector<int> includes_;
  LinColQuery lincol_;

public:
  PreProcessor(std::string input) : buffer(std::move(input)) {}

  // Get the text content of a token
  std::string getTokenText(const Token &token) const {
    if (token.begin + token.len > buffer.size()) {
      return "";
    }
    return std::string(buffer.c_str() + token.begin, token.len);
  }

  // Get the current buffer (for testing purposes)
  const std::string &getBuffer() const { return buffer; }

  // Expand macros in the input and return the result
  std::string expandMacros() {
    // Create a new buffer with processed content
    std::string processedBuffer = processAndExpand();
    return processedBuffer;
  }

  std::string processAndExpand() {
    std::ostringstream result;

    while (cursor < buffer.size()) {
      Token token = next();
      if (token.kind == TokenKind::T_EOF) {
        break;
      }

      // Handle preprocessor directives
      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::Include) {
          handle_include();
        } else if (directive.kind == TokenKind::Define) {
          handle_define();
        } else if (directive.kind == TokenKind::Undef) {
          handle_undef();
        } else if (directive.kind == TokenKind::If) {
          handle_if_with_expansion(result);
        } else if (directive.kind == TokenKind::Else) {
          handle_else();
        } else if (directive.kind == TokenKind::Endif) {
          handle_endif();
        }
        continue;
      }

      // Handle newlines
      if (token.kind == TokenKind::Unknown) {
        result << "\n";
        continue;
      }

      // Check if this identifier is a macro
      if (token.kind == TokenKind::Ident) {
        std::string tokenText = getTokenText(token);

        // Check for function macro first
        if (functionMacros.find(tokenText) != functionMacros.end()) {
          // Look ahead to see if there's a '('
          unsigned savedCursor = cursor;
          skip_whitespace_and_comments();

          if (cursor < buffer.size() && buffer[cursor] == '(') {
            std::string expanded = expandFunctionMacro(tokenText);
            result << expanded;
            continue;
          } else {
            // Not a function call, restore cursor and treat as regular
            // identifier
            cursor = savedCursor;
            // Fall through to regular token processing
          }
        }

        // Check for object macro
        if (macros.find(tokenText) != macros.end()) {
          result << macros[tokenText];
          continue;
        }
      }

      // Regular token - add with appropriate spacing
      std::string tokenText = getTokenText(token);

      // Add space before certain operators
      if (token.kind == TokenKind::Assign || token.kind == TokenKind::Plus ||
          token.kind == TokenKind::Minus || token.kind == TokenKind::Star ||
          token.kind == TokenKind::Slash) {
        result << " ";
      }

      result << tokenText;

      // Add space after certain tokens for readability, but not before
      // semicolons or when the next token starts with certain characters
      if ((token.kind == TokenKind::Ident || token.kind == TokenKind::Number ||
           token.kind == TokenKind::Assign || token.kind == TokenKind::Plus ||
           token.kind == TokenKind::Minus || token.kind == TokenKind::Star ||
           token.kind == TokenKind::Slash) &&
          cursor < buffer.size() && buffer[cursor] != ';' &&
          buffer[cursor] != '(' && buffer[cursor] != ')') {
        result << " ";
      }

      // Add space after semicolon
      if (token.kind == TokenKind::Semicolon) {
        result << " ";
      }
    }

    return result.str();
  }

  // Tokenize the input buffer
  Token next() {
    skip_whitespace_and_comments();

    if (cursor >= buffer.size()) {
      return {cursor, 0, TokenKind::T_EOF};
    }

    unsigned start = cursor;
    char c = buffer[cursor];

    // Newline
    if (c == '\n') {
      cursor++;

      lincol_.addLine(cursor);

      return {start, 1, TokenKind::Unknown};
    }

    // Identifier or Keyword
    if (std::isalpha(c) || c == '_') {
      while (cursor < buffer.size() &&
             (std::isalnum(buffer[cursor]) || buffer[cursor] == '_')) {
        cursor++;
      }
      std::string_view value =
          std::string_view(buffer.c_str() + start, cursor - start);
      if (value == "include")
        return {start, cursor - start, TokenKind::Include};
      if (value == "define")
        return {start, cursor - start, TokenKind::Define};
      if (value == "undef")
        return {start, cursor - start, TokenKind::Undef};
      if (value == "if")
        return {start, cursor - start, TokenKind::If};
      if (value == "else")
        return {start, cursor - start, TokenKind::Else};
      if (value == "endif")
        return {start, cursor - start, TokenKind::Endif};
      return {start, cursor - start, TokenKind::Ident};
    }

    // Number
    if (std::isdigit(c)) {
      while (cursor < buffer.size() && std::isdigit(buffer[cursor])) {
        cursor++;
      }
      return {start, cursor - start, TokenKind::Number};
    }

    // String Literal
    if (c == '"') {
      cursor++;
      while (cursor < buffer.size() && buffer[cursor] != '"') {
        if (buffer[cursor] == '\\')
          cursor++; // Skip escaped characters
        cursor++;
      }
      if (cursor < buffer.size())
        cursor++; // Skip closing quote
      return {start, cursor - start, TokenKind::StringLiteral};
    }

    // Hash (#)
    if (c == '#') {
      cursor++;
      if (cursor < buffer.size() && buffer[cursor] == '#') {
        cursor++;
        return {start, 2, TokenKind::HashHash};
      }
      return {start, 1, TokenKind::Hash};
    }

    // Punctuators
    cursor++;
    // Punctuators
    if (c == '[')
      return {start, 1, TokenKind::L_Bracket};
    if (c == ']')
      return {start, 1, TokenKind::R_Bracket};
    if (c == '(')
      return {start, 1, TokenKind::L_Paren};
    if (c == ')')
      return {start, 1, TokenKind::R_Paren};
    if (c == '{')
      return {start, 1, TokenKind::L_Brace};
    if (c == '}')
      return {start, 1, TokenKind::R_Brace};
    if (c == '.') {
      if (cursor + 2 < buffer.size() && buffer[cursor] == '.' &&
          buffer[cursor + 1] == '.') {
        cursor += 2;
        return {start, 3, TokenKind::Ellipsis};
      }
      return {start, 1, TokenKind::Dot};
    }
    if (c == '-' && cursor < buffer.size() && buffer[cursor] == '>') {
      cursor++;
      return {start, 2, TokenKind::Arrow};
    }
    if (c == '+' && cursor < buffer.size() && buffer[cursor] == '+') {
      cursor++;
      return {start, 2, TokenKind::PlusPlus};
    }
    if (c == '-' && cursor < buffer.size() && buffer[cursor] == '-') {
      cursor++;
      return {start, 2, TokenKind::MinusMinus};
    }
    if (c == '&' && cursor < buffer.size() && buffer[cursor] == '&') {
      cursor++;
      return {start, 2, TokenKind::LogicAnd};
    }
    if (c == '|' && cursor < buffer.size() && buffer[cursor] == '|') {
      cursor++;
      return {start, 2, TokenKind::LogicOr};
    }
    if (c == '<' && cursor < buffer.size() && buffer[cursor] == '<') {
      cursor++;
      if (cursor < buffer.size() && buffer[cursor] == '=') {
        cursor++;
        return {start, 3, TokenKind::LessLessEqual};
      }
      return {start, 2, TokenKind::LessLess};
    }
    if (c == '>' && cursor < buffer.size() && buffer[cursor] == '>') {
      cursor++;
      if (cursor < buffer.size() && buffer[cursor] == '=') {
        cursor++;
        return {start, 3, TokenKind::GreaterGreaterEqual};
      }
      return {start, 2, TokenKind::GreaterGreater};
    }
    if (c == '<' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::LessEqual};
    }
    if (c == '>' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::GreaterEqual};
    }
    if (c == '=' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::EqualEqual};
    }
    if (c == '!' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::ExclamationEqual};
    }
    if (c == '*' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::MulAssign};
    }
    if (c == '/' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::DivAssign};
    }
    if (c == '%' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::ModAssign};
    }
    if (c == '+' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::AddAssign};
    }
    if (c == '-' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::MinusEqual};
    }
    if (c == '&' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::BitAndEqual};
    }
    if (c == '^' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::XorAssign};
    }
    if (c == '|' && cursor < buffer.size() && buffer[cursor] == '=') {
      cursor++;
      return {start, 2, TokenKind::OrAssign};
    }
    if (c == '&')
      return {start, 1, TokenKind::Ampersand};
    if (c == '*')
      return {start, 1, TokenKind::Star};
    if (c == '+')
      return {start, 1, TokenKind::Plus};
    if (c == '-')
      return {start, 1, TokenKind::Minus};
    if (c == '~')
      return {start, 1, TokenKind::Tilde};
    if (c == '!')
      return {start, 1, TokenKind::Not};
    if (c == '/')
      return {start, 1, TokenKind::Slash};
    if (c == '%')
      return {start, 1, TokenKind::Percent};
    if (c == '<')
      return {start, 1, TokenKind::Less};
    if (c == '>')
      return {start, 1, TokenKind::Greater};
    if (c == '^')
      return {start, 1, TokenKind::XOR};
    if (c == '|')
      return {start, 1, TokenKind::BitOr};
    if (c == '?')
      return {start, 1, TokenKind::Question};
    if (c == ':')
      return {start, 1, TokenKind::Colon};
    if (c == ';')
      return {start, 1, TokenKind::Semicolon};
    if (c == '=')
      return {start, 1, TokenKind::Assign};
    if (c == ',')
      return {start, 1, TokenKind::Comma};

    // If no match, return unknown punctuator
    return {start, 1, TokenKind::Unknown};
  }

  // Process the buffer and handle preprocessor directives
  void process() {
    while (true) {
      Token token = next();
      if (token.kind == TokenKind::T_EOF)
        break;

      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::Include) {
          handle_include();
        } else if (directive.kind == TokenKind::Define) {
          handle_define();
        } else if (directive.kind == TokenKind::Undef) {
          handle_undef();
        } else if (directive.kind == TokenKind::If) {
          handle_if();
        } else if (directive.kind == TokenKind::Else) {
          handle_else();
        } else if (directive.kind == TokenKind::Endif) {
          handle_endif();
        } else {
          assert(0 && "unexpect kind");
        }
      }
    }
  }

private:
  void skip_whitespace_and_comments() {
    while (cursor < buffer.size()) {
      if (std::isspace(buffer[cursor]) && buffer[cursor] != '\n') {
        cursor++;
        continue;
      }
      // Single-line comment
      if (cursor + 1 < buffer.size() && buffer[cursor] == '/' &&
          buffer[cursor + 1] == '/') {
        while (cursor < buffer.size() && buffer[cursor] != '\n') {
          cursor++;
        }
        continue;
      }
      // Multi-line comment
      if (cursor + 1 < buffer.size() && buffer[cursor] == '/' &&
          buffer[cursor + 1] == '*') {
        cursor += 2;
        while (cursor + 1 < buffer.size() &&
               !(buffer[cursor] == '*' && buffer[cursor + 1] == '/')) {
          cursor++;
        }
        if (cursor + 1 < buffer.size()) {
          cursor += 2;
        }
        continue;
      }
      break;
    }
  }

  void handle_include() {
    Token header = next();

    if (header.kind != TokenKind::StringLiteral) {
      throw std::runtime_error("Expected a header name after #include");
    }
  }

  void handle_define() {
    Token name = next();
    if (name.kind != TokenKind::Ident) {
      throw std::runtime_error("Expected identifier after #define");
    }

    std::string macroName = get_token_text(name);

    // Check if it's a function-like macro
    if (cursor < buffer.size() && buffer[cursor] == '(') {
      handle_function_macro(macroName);
    } else {
      handle_object_macro(macroName);
    }
  }

  void handle_undef() {
    Token name = next();
    if (name.kind != TokenKind::Ident) {
      throw std::runtime_error("Expected identifier after #undef");
    }

    std::string macroName = get_token_text(name);
    macros.erase(macroName);
    functionMacros.erase(macroName);
  }

  void handle_if() {
    // For now, implement a simple version that evaluates constant expressions
    // Skip to end of line and evaluate the condition
    std::string condition = read_line();

    // Simple evaluation - check if macro is defined or if it's a number != 0
    bool result = evaluate_condition(condition);

    if (!result) {
      skip_until_else_or_endif();
    }
  }

  void handle_else() {
    // Skip until #endif since we're in the else branch
    skip_until_endif();
  }

  void handle_endif() {
    // Nothing to do - just marks the end of conditional block
  }

  // Helper functions
  std::string get_token_text(const Token &token) {
    return std::string(buffer.c_str() + token.begin, token.len);
  }

  void handle_object_macro(const std::string &macroName) {
    skip_whitespace_and_comments();

    // Read the replacement text until end of line
    std::string replacement = read_line();
    macros[macroName] = replacement;
  }

  void handle_function_macro(const std::string &macroName) {
    // Skip the opening parenthesis
    cursor++;

    std::vector<std::string> parameters;

    // Parse parameters
    while (cursor < buffer.size()) {
      skip_whitespace_and_comments();

      if (cursor < buffer.size() && buffer[cursor] == ')') {
        cursor++;
        break;
      }

      Token param = next();
      if (param.kind != TokenKind::Ident) {
        throw std::runtime_error("Expected parameter name in function macro");
      }

      parameters.push_back(get_token_text(param));

      skip_whitespace_and_comments();
      if (cursor < buffer.size() && buffer[cursor] == ',') {
        cursor++;
      } else if (cursor < buffer.size() && buffer[cursor] == ')') {
        cursor++;
        break;
      }
    }

    // Read the replacement text
    std::string replacement = read_line();

    // Store the function macro
    functionMacros[macroName] = parameters;
    // Store replacement text separately for function macros
    functionMacroReplacements[macroName] = replacement;
  }

  std::string read_line() {
    std::string line;
    while (cursor < buffer.size() && buffer[cursor] != '\n') {
      line += buffer[cursor];
      cursor++;
    }
    // Trim trailing whitespace
    while (!line.empty() && std::isspace(line.back())) {
      line.pop_back();
    }
    return line;
  }

  bool evaluate_condition(const std::string &condition) {
    // Simple condition evaluation
    std::string trimmed = condition;

    // Remove leading/trailing whitespace
    size_t start = trimmed.find_first_not_of(" \t");
    if (start == std::string::npos)
      return false;

    size_t end = trimmed.find_last_not_of(" \t");
    trimmed = trimmed.substr(start, end - start + 1);

    // Check for "defined(MACRO)" syntax first
    if (trimmed.find("defined(") == 0 && trimmed.back() == ')') {
      std::string macroName = trimmed.substr(8, trimmed.length() - 9);
      return macros.find(macroName) != macros.end() ||
             functionMacros.find(macroName) != functionMacros.end();
    }

    // Expand macros in the condition before evaluation
    std::string expandedCondition = expandMacrosInCondition(trimmed);

    // Check if it's a number after expansion
    if (!expandedCondition.empty() &&
        (std::isdigit(expandedCondition[0]) || expandedCondition[0] == '-')) {
      try {
        int value = std::stoi(expandedCondition);
        return value != 0;
      } catch (...) {
        return false;
      }
    }

    // If it's still an identifier after expansion, it's undefined (false)
    return false;
  }

  void skip_until_else_or_endif() {
    int depth = 1;

    while (cursor < buffer.size() && depth > 0) {
      Token token = next();

      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::If) {
          depth++;
        } else if (directive.kind == TokenKind::Endif) {
          depth--;
        } else if (directive.kind == TokenKind::Else && depth == 1) {
          return; // Found matching else
        }
      }
    }
  }

  void skip_until_endif() {
    int depth = 1;

    while (cursor < buffer.size() && depth > 0) {
      Token token = next();

      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::If) {
          depth++;
        } else if (directive.kind == TokenKind::Endif) {
          depth--;
        }
      }
    }
  }

  void handle_if_with_expansion(std::ostringstream &result) {
    // Read and evaluate the condition
    std::string condition = read_line();
    bool conditionResult = evaluate_condition(condition);

    if (conditionResult) {
      // Process the true branch
      processConditionalBlock(result, true);
    } else {
      // Skip the true branch and look for else
      skipConditionalBlock();

      // Check if there's an else clause
      unsigned savedCursor = cursor;
      if (findMatchingElse()) {
        // Process the else branch
        processConditionalBlock(result, false);
      } else {
        cursor = savedCursor;
      }
    }
  }

  void processConditionalBlock(std::ostringstream &result, bool isIfBranch) {
    int depth = 1;

    while (cursor < buffer.size() && depth > 0) {
      Token token = next();
      if (token.kind == TokenKind::T_EOF) {
        break;
      }

      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::If) {
          depth++;
          // Handle nested #if by recursively processing it
          handle_if_with_expansion(result);
          depth--; // The recursive call handles the entire nested block
        } else if (directive.kind == TokenKind::Endif) {
          depth--;
          if (depth == 0) {
            return; // End of our conditional block
          }
        } else if (directive.kind == TokenKind::Else && depth == 1) {
          if (isIfBranch) {
            return; // End of if branch, don't process else
          }
        } else {
          // Other directives - process them
          if (directive.kind == TokenKind::Define) {
            handle_define();
          } else if (directive.kind == TokenKind::Undef) {
            handle_undef();
          }
        }
        continue;
      }

      // Handle newlines
      if (token.kind == TokenKind::Unknown) {
        result << "\n";
        continue;
      }

      // Process regular tokens with macro expansion
      if (token.kind == TokenKind::Ident) {
        std::string tokenText = getTokenText(token);

        // Check for function macro first
        if (functionMacros.find(tokenText) != functionMacros.end()) {
          unsigned savedCursor = cursor;
          skip_whitespace_and_comments();

          if (cursor < buffer.size() && buffer[cursor] == '(') {
            std::string expanded = expandFunctionMacro(tokenText);
            result << expanded;
            continue;
          } else {
            cursor = savedCursor;
          }
        }

        // Check for object macro
        if (macros.find(tokenText) != macros.end()) {
          result << macros[tokenText];
          continue;
        }
      }

      // Regular token
      std::string tokenText = getTokenText(token);

      // Add space before certain operators
      if (token.kind == TokenKind::Assign || token.kind == TokenKind::Plus ||
          token.kind == TokenKind::Minus || token.kind == TokenKind::Star ||
          token.kind == TokenKind::Slash) {
        result << " ";
      }

      result << tokenText;

      // Add space after certain tokens for readability
      if ((token.kind == TokenKind::Ident || token.kind == TokenKind::Number ||
           token.kind == TokenKind::Assign || token.kind == TokenKind::Plus ||
           token.kind == TokenKind::Minus || token.kind == TokenKind::Star ||
           token.kind == TokenKind::Slash) &&
          cursor < buffer.size() && buffer[cursor] != ';' &&
          buffer[cursor] != '(' && buffer[cursor] != ')') {
        result << " ";
      }

      // Add space after semicolon
      if (token.kind == TokenKind::Semicolon) {
        result << " ";
      }
    }
  }

  void skipConditionalBlock() {
    int depth = 1;

    while (cursor < buffer.size() && depth > 0) {
      Token token = next();

      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::If) {
          depth++;
        } else if (directive.kind == TokenKind::Endif) {
          depth--;
        } else if (directive.kind == TokenKind::Else && depth == 1) {
          return; // Found matching else
        }
      }
    }
  }

  bool findMatchingElse() {
    unsigned savedCursor = cursor;

    // Look for #else at the same nesting level
    while (cursor < buffer.size()) {
      Token token = next();

      if (token.kind == TokenKind::Hash) {
        Token directive = next();
        if (directive.kind == TokenKind::Else) {
          return true; // Found else
        } else if (directive.kind == TokenKind::Endif) {
          cursor = savedCursor;
          return false; // Found endif without else
        }
      }
    }

    cursor = savedCursor;
    return false;
  }

  void skipDirectiveLine() {
    // Skip tokens until we hit EOF or newline
    while (cursor < buffer.size()) {
      Token token = next();
      if (token.kind == TokenKind::T_EOF || token.kind == TokenKind::Unknown) {
        break;
      }
    }
  }

  std::string expandMacrosInCondition(const std::string &condition) {
    // Simple macro expansion for conditions
    std::string result = condition;

    // Check if the entire condition is a macro name
    if (macros.find(result) != macros.end()) {
      return macros[result];
    }

    // For more complex expressions, we'd need a proper tokenizer
    // For now, just return the original condition
    return result;
  }

  std::string expandFunctionMacro(const std::string &macroName) {
    // Check if next token is '('
    skip_whitespace_and_comments();
    if (cursor >= buffer.size() || buffer[cursor] != '(') {
      // Not a function call, treat as identifier
      return macroName;
    }

    cursor++; // Skip '('

    // Parse arguments
    std::vector<std::string> args;
    std::string currentArg;
    int parenDepth = 0;

    while (cursor < buffer.size()) {
      char c = buffer[cursor];

      if (c == '(') {
        parenDepth++;
        currentArg += c;
      } else if (c == ')') {
        if (parenDepth == 0) {
          // End of function call
          if (!currentArg.empty()) {
            args.push_back(currentArg);
          }
          cursor++; // Skip closing ')'
          break;
        } else {
          parenDepth--;
          currentArg += c;
        }
      } else if (c == ',' && parenDepth == 0) {
        // Argument separator
        args.push_back(currentArg);
        currentArg.clear();
      } else {
        currentArg += c;
      }

      cursor++;
    }

    // Get the macro replacement text
    if (functionMacroReplacements.find(macroName) ==
        functionMacroReplacements.end()) {
      return macroName; // Macro not found
    }

    std::string replacement = functionMacroReplacements[macroName];

    // Simple parameter substitution
    if (functionMacros.find(macroName) != functionMacros.end()) {
      const auto &params = functionMacros[macroName];

      for (size_t i = 0; i < params.size() && i < args.size(); i++) {
        // Replace parameter with argument in replacement text
        std::string param = params[i];
        std::string arg = args[i];

        // Trim whitespace from argument
        size_t start = arg.find_first_not_of(" \t");
        size_t end = arg.find_last_not_of(" \t");
        if (start != std::string::npos) {
          arg = arg.substr(start, end - start + 1);
        }

        // Simple string replacement
        size_t pos = 0;
        while ((pos = replacement.find(param, pos)) != std::string::npos) {
          replacement.replace(pos, param.length(), arg);
          pos += arg.length();
        }
      }
    }

    return replacement;
  }
};
