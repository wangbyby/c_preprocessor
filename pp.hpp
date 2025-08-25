#pragma once

#include <string>
#include <vector>
#include <map>
#include <stdexcept>
#include <sstream>
#include <fstream>
#include <iostream>
#include <optional>
#include <cctype>

// TokenKind: Represents the type of tokens in the preprocessor
enum class TokenKind {
    T_EOF = -1,
    T_Unknown = 0,
    T_Identifier,
    T_Number,
    T_StringLiteral,
    T_CharLiteral,
    T_Punctuator,
    T_Hash,       // #
    T_HashHash,   // ##
    T_Include,    // include
    T_Define,     // define
    T_Undef,      // undef
    T_If,         // if
    T_Else,       // else
    T_Endif,      // endif
};

// Token: Represents a single token
struct Token {
    unsigned begin;
    unsigned len;
    TokenKind kind;
    std::string value;

    Token(unsigned b, unsigned l, TokenKind k, std::string v)
        : begin(b), len(l), kind(k), value(std::move(v)) {}
};

// PreProcessor: The main class for the preprocessor
class PreProcessor {
private:
    std::string buffer;
    unsigned cursor = 0;
    std::map<std::string, std::string> macros; // Stores object macros
    std::map<std::string, std::vector<std::string>> functionMacros; // Stores function macros

public:
    PreProcessor(std::string input) : buffer(std::move(input)) {}

    // Tokenize the input buffer
    Token next() {
        skip_whitespace_and_comments();

        if (cursor >= buffer.size()) {
            return {cursor, 0, TokenKind::T_EOF, ""};
        }

        unsigned start = cursor;
        char c = buffer[cursor];

        // Newline
        if (c == '\n') {
            cursor++;
            return {start, 1, TokenKind::T_Newline, "\n"};
        }

        // Identifier or Keyword
        if (std::isalpha(c) || c == '_') {
            while (cursor < buffer.size() && (std::isalnum(buffer[cursor]) || buffer[cursor] == '_')) {
                cursor++;
            }
            std::string value = buffer.substr(start, cursor - start);
            if (value == "include") return {start, cursor - start, TokenKind::T_Include, value};
            if (value == "define") return {start, cursor - start, TokenKind::T_Define, value};
            if (value == "undef") return {start, cursor - start, TokenKind::T_Undef, value};
            if (value == "if") return {start, cursor - start, TokenKind::T_If, value};
            if (value == "else") return {start, cursor - start, TokenKind::T_Else, value};
            if (value == "endif") return {start, cursor - start, TokenKind::T_Endif, value};
            return {start, cursor - start, TokenKind::T_Identifier, value};
        }

        // Number
        if (std::isdigit(c)) {
            while (cursor < buffer.size() && std::isdigit(buffer[cursor])) {
                cursor++;
            }
            return {start, cursor - start, TokenKind::T_Number, buffer.substr(start, cursor - start)};
        }

        // String Literal
        if (c == '"') {
            cursor++;
            while (cursor < buffer.size() && buffer[cursor] != '"') {
                if (buffer[cursor] == '\\') cursor++; // Skip escaped characters
                cursor++;
            }
            if (cursor < buffer.size()) cursor++; // Skip closing quote
            return {start, cursor - start, TokenKind::T_StringLiteral, buffer.substr(start, cursor - start)};
        }

        // Hash (#)
        if (c == '#') {
            cursor++;
            if (cursor < buffer.size() && buffer[cursor] == '#') {
                cursor++;
                return {start, 2, TokenKind::T_HashHash, "##"};
            }
            return {start, 1, TokenKind::T_Hash, "#"};
        }

        // Punctuators
        cursor++;
        return {start, 1, TokenKind::T_Punctuator, buffer.substr(start, 1)};
    }

    // Process the buffer and handle preprocessor directives
    void process() {
        while (true) {
            Token token = next();
            if (token.kind == TokenKind::T_EOF) break;

            if (token.kind == TokenKind::T_Hash) {
                Token directive = next();
                if (directive.kind == TokenKind::T_Include) {
                    handle_include();
                } else if (directive.kind == TokenKind::T_Define) {
                    handle_define();
                } else if (directive.kind == TokenKind::T_Undef) {
                    handle_undef();
                } else if (directive.kind == TokenKind::T_If) {
                    handle_if();
                } else if (directive.kind == TokenKind::T_Else) {
                    handle_else();
                } else if (directive.kind == TokenKind::T_Endif) {
                    handle_endif();
                } else {
                    throw std::runtime_error("Unknown preprocessor directive: " + directive.value);
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
            if (cursor + 1 < buffer.size() && buffer[cursor] == '/' && buffer[cursor + 1] == '/') {
                while (cursor < buffer.size() && buffer[cursor] != '\n') {
                    cursor++;
                }
                continue;
            }
            // Multi-line comment
            if (cursor + 1 < buffer.size() && buffer[cursor] == '/' && buffer[cursor + 1] == '*') {
                cursor += 2;
                while (cursor + 1 < buffer.size() && !(buffer[cursor] == '*' && buffer[cursor + 1] == '/')) {
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
        if (header.kind != TokenKind::T_StringLiteral) {
            throw std::runtime_error("Expected a header name after #include");
        }
        std::ifstream file(header.value.substr(1, header.value.size() - 2)); // Remove quotes
        if (!file) {
            throw std::runtime_error("Failed to open file: " + header.value);
        }
        std::stringstream ss;
        ss << file.rdbuf();
        buffer.insert(cursor, ss.str());
    }

    void handle_define() {
        Token name = next();
        if (name.kind != TokenKind::T_Identifier) {
            throw std::runtime_error("Expected an identifier after #define");
        }
        Token value = next();
        macros[name.value] = value.value;
    }

    void handle_undef() {
        Token name = next();
        if (name.kind != TokenKind::T_Identifier) {
            throw std::runtime_error("Expected an identifier after #undef");
        }
        macros.erase(name.value);
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
