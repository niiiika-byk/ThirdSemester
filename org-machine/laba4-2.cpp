//использованием библиотеки стандарта OpenMP
#include <iostream>
#include <vector>
#include <random>
#include <chrono>
#include <omp.h> //OpenMP

using dtype = double;

int main(int argc, char** argv) {
    if(argc<3) { std::cerr<<"Usage: "<<argv[0]<<" N num_threads\n"; return 1; }
    int N = std::stoi(argv[1]);
    int nthreads = std::stoi(argv[2]);
    std::vector<dtype> A(N*N), B(N*N), C(N*N);

    std::mt19937_64 rng(0);
    std::uniform_real_distribution<dtype> dist(0.0,1.0);
    for(int i=0;i<N*N;++i){ A[i]=dist(rng); B[i]=dist(rng); C[i]=0; }

    omp_set_num_threads(nthreads);
    auto t0 = std::chrono::high_resolution_clock::now();

#pragma omp parallel for collapse(2) schedule(static)
    for(int i=0;i<N;++i) {
        for(int j=0;j<N;++j) {
            dtype sum = 0;
            for(int k=0;k<N;++k)
                sum += A[i*N + k] * B[k*N + j];
            C[i*N + j] = sum;
        }
    }

    auto t1 = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> dt = t1 - t0;
    std::cout<<"openmp, "<<N<<", "<<nthreads<<", "<<dt.count()<<"\n";
    return 0;
}
