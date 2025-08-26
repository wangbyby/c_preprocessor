#include "pp.hpp"
#include <iostream>

int main() {
    std::cout << "Starting simple test..." << std::endl;
    std::cout.flush();
    
    try {
        std::string input = "#define PI 3.14159\n";
        std::cout << "Creating preprocessor with input: " << input << std::endl;
        
        PreProcessor pp(input);
        std::cout << "Processing..." << std::endl;
        pp.process();
        std::cout << "Processing completed successfully!" << std::endl;
        
    } catch (const std::exception& e) {
        std::cout << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    std::cout << "Test finished!" << std::endl;
    return 0;
}