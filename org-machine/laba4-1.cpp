//использование библиотеки стандарта POSIX Threads
#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <pthread.h> //posix threads
#include <cstring>

using dtype = double;

struct ThreadArgs {
    const dtype* A;
    const dtype* B;
    dtype* C;
    int N;
    int idx;
    int nthreads;
};

void* worker(void* v) {
    auto* args = static_cast<ThreadArgs*>(v);
    int N = args->N;
    int per = N / args->nthreads;
    int start = args->idx * per;
    int end   = (args->idx == args->nthreads - 1) ? N : start + per;

    // Инициализация своего блока C[start..end), B и A разделяются на все потоки
    // (инициализировать A,B можно одним потоком, но тут делаем внутри каждого для демонстрации)
    std::mt19937_64 rng(args->idx);
    std::uniform_real_distribution<dtype> dist(0.0, 1.0);
    for(int i = start; i < end; ++i) {
        for(int j = 0; j < N; ++j) {
            args->C[i*N + j] = 0.0;
        }
    }

    // Умножение
    for(int i = start; i < end; ++i) {
        for(int j = 0; j < N; ++j) {
            dtype sum = 0;
            for(int k = 0; k < N; ++k) {
                sum += args->A[i*N + k] * args->B[k*N + j];
            }
            args->C[i*N + j] = sum;
        }
    }
    return nullptr;
}

int main(int argc, char** argv) {
    if(argc < 3) {
        std::cerr << "Usage: "<< argv[0] << " N num_threads\n";
        return 1;
    }
    int N = std::stoi(argv[1]);
    int nthreads = std::stoi(argv[2]);

    std::vector<dtype> A(N*N), B(N*N), C(N*N);
    // Инициализация A и B случайными числами (одним потоком)
    std::mt19937_64 rng(0);
    std::uniform_real_distribution<dtype> dist(0.0,1.0);
    for(int i=0;i<N*N;++i) {
        A[i] = dist(rng);
        B[i] = dist(rng);
    }

    std::vector<pthread_t> threads(nthreads);
    std::vector<ThreadArgs> args(nthreads);
    for(int t=0;t<nthreads;++t) {
        args[t] = {A.data(), B.data(), C.data(), N, t, nthreads};
        pthread_create(&threads[t], nullptr, worker, &args[t]);
    }
    auto t0 = std::chrono::high_resolution_clock::now();
    for(int t=0;t<nthreads;++t)
        pthread_join(threads[t], nullptr);
    auto t1 = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> dt = t1 - t0;
    std::cout << "pthreads, "<<N<<", "<<nthreads<<", "<< dt.count() <<"\n";
    return 0;
}
