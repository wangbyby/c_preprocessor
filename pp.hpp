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
  Endif,   // #endif

  // literals
  Number,
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

  Hash,    // #
  HashHash // ##
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

  std::vector<int> includes_;
  LinColQuery lincol_;

public:
  PreProcessor(std::string input) : buffer(std::move(input)) {}

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
    // TODO
  }

  void handle_undef() {
    // TODO
  }

  void handle_if() {
    // TODO: Implement conditional compilation
  }

  void handle_else() {
    // TODO: Implement conditional compilation
  }

  void handle_endif() {
    // TODO: Implement conditional compilation
  }
};
