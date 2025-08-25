

# 实现C99标准的预处理器


## 实现
必须用CPP17实现，one header only

## 结构体定义

```cpp
enum TokenKind {
    T_EOF = -1,
    T_Unknown = 0,
    .....// TODO, fill this

};

struct Token{
    unsigned begin;
    unsigned len;
    TokenKind kind;
};


class PreProcessor{
    std::string buffer;


    Token next() {
        // TODO implement this
    }
};


```

1. TokenKind 是token的类别，用枚举实现，包括所有c99中定义的preprocessor tokens，特别是包括#和##
2. Token代表一个词法单元，begin是在buffer的开始index，
3. PreProcessor是预处理器的主要类，buffer是缓冲区暂时定义为一次性从文件中读取所有内容
 3.1 对外提供的接口是迭代式的，如果到buffer结束，就返回Token：：EOF
 3.2 PreProcessor必须要处理include，define，undef，if，else 等宏功能
 3.3 此外也需要实现对象宏，和函数宏

4. 测试
需要编写测试用例测试include，define，undef，if，else等功能
