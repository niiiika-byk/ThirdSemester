#include <iostream>
#include <vector>
#include <iomanip>
#include <random>
#include <string>
#include <chrono>

using namespace std;

void print_matrix(const std::vector<double>& matrix, int size) {
    for (int i = 0; i < size; i++) {
        for (int j = 0; j < size; j++) {
            std::cout << std::setw(10) << matrix[i * size + j] << " ";
        }
        std::cout << std::endl;
    }
}

void dgemm(const std::vector<double>& a, const std::vector<double>& b, std::vector<double> &result, const int size) {
    int i, j, k;
    for (i = 0; i < size; i++) {
        for (j = 0; j < size; j++) {
            for (k = 0; k < size; k++) {
                result[i * size + j] += a[i * size + k] * b[k * size + j];
            }
        }
    }
}

void dgemm_opt1(std::vector<double>& a, std::vector<double>& b, std::vector<double> &result, const int size) {
    int i, j, k;
    for (i = 0; i < size; i++) {
        for (k = 0; k < size; k++) {
            double aik = a[i * size + k];
            for (j = 0; j < size; j++) {
                result[i * size + j] += aik * b[k * size + j];
            }
        }
    }
}

void dgemm_opt2(const std::vector<double>& a, const std::vector<double>& b, std::vector<double>& result, const int size, const int block_size) {
    for (int i = 0; i < size; i += block_size) {
        for (int j = 0; j < size; j += block_size) {
            for (int k = 0; k < size; k += block_size) {
                for (int i1 = i; i1 < i + block_size && i1 < size; ++i1) {
                    for (int j1 = j; j1 < j + block_size && j1 < size; ++j1) {
                        double sum = 0.0;
                        for (int k1 = k; k1 < k + block_size && k1 < size; ++k1) {
                            sum += a[i1 * size + k1] * b[k1 * size + j1];
                        }
                        result[i1 * size + j1] += sum;
                    }
                }
            }
        }
    }
}

int main(int argc, char *argv[]) {
    if (argc < 2 || argc > 5) {
        std::cout << "Usage: " << argv[0] << " <matrix size> [-o] [-t] [--opt0] [--opt1] [--opt2=<block_size>]" << std::endl;
        std::cout << "Help: \n"
        << "-o        print all matrix on screen\n"
        << "-t        timer\n"
        << "--opt0    default func dgemm blass\n"
        << "--opt1    optimization by line-by-line iteration of elements\n"
        << "--opt2    optimization due to block iteration of matrix elements, you can specify block size\n";
        return 0;
    }

    bool output = false;
    bool timer = false;
    int type_of_func = -1;
    int block_size = 2;// размер блока задаем на случай, если не задаст пользователь

    for (auto i = 2; i < argc; i++) {
        if (std::string(argv[i]) == "-o") 
            output = true;
        else if (std::string(argv[i]) == "-t") 
            timer = true;
        else if (type_of_func == -1) {
            if (std::string(argv[i]) == "--opt0")  
                type_of_func = 0;
            else if (std::string(argv[i]) == "--opt1") 
                type_of_func = 1;
            else if (std::string(argv[i]).find("--opt2=") == 0) {
                type_of_func = 2;
                std::string num = std::string(argv[i]).substr(7); 
                if(std::stoi(num) && std::stoi(num) > 0)
                    block_size = std::stoi(num);
            }       
        }
    }

    srand(time(NULL));

    int n = atoi(argv[1]);

    std::vector<double> a(n*n);
    std::vector<double> b(n*n);
    
    // генератор случайных чисел и распределение для этих чисел
    std::mt19937 gen(42);
    std::uniform_real_distribution<double> dist(0.0, 1.0);

    // заполнение случайными числами
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) {
            a[i * n + j] = dist(gen);
            b[i * n + j] = dist(gen);
        }
    }

    // Создаем пустую матрицу для результата
    std::vector<double> result(n*n, 0.0);

    std::chrono::time_point<std::chrono::system_clock> start;
    std::chrono::time_point<std::chrono::system_clock> end;

    switch (type_of_func)
    {
    case 0: { 
        start = std::chrono::system_clock::now();
        dgemm(a, b, result, n);
        end = std::chrono::system_clock::now();
        break;
    }
    case 1: { 
        start = std::chrono::system_clock::now();
        dgemm_opt1(a, b, result, n);
        end = std::chrono::system_clock::now();
        break;
    }
    case 2: {  
        start = std::chrono::system_clock::now();
        dgemm_opt2(a, b, result, n, block_size);
        end = std::chrono::system_clock::now();
        break;
    }
    default:
        std::cout << "You didn\'t choose type of functions";
        exit(0);
    }

    //если задан флаг с подсчетом времени работы кода, то вычисляем его и выводим на экран
    if (timer) 
        std::cout << std::chrono::duration <double, std::milli> (end-start).count() << " ms" << std::endl;
    
    if (output) {
        std::cout << "Matrix A:" << std::endl;
        print_matrix(a,n);

        std::cout << "Matrix B:" << std::endl;
        print_matrix(b,n);

        std::cout << "Matrix C = A * B:" << std::endl;
        print_matrix(result,n);
    }

    return 0;
}
