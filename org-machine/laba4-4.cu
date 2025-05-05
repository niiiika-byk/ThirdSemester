//технологий многопоточности для графических сопроцессоров (GPU) - CUDA
#include <iostream>
#include <string>
#include <vector>
#include <random>
#include <chrono>
#include <cuda_runtime.h>

using namespace std;
typedef double dtype;

__global__ void kern_dgemm(const dtype* A, const dtype* B, dtype* C, int N) {
    int i = blockIdx.y * blockDim.y + threadIdx.y;
    int j = blockIdx.x * blockDim.x + threadIdx.x;
    if(i<N && j<N) {
        dtype sum = 0;
        for(int k=0;k<N;++k)
            sum += A[i*N + k] * B[k*N + j];
        C[i*N + j] = sum;
    }
}

int main(int argc, char** argv) {
    if(argc<2){ cerr<<"Usage: "<<argv[0]<<" N\n"; return 1; }
    int N = stoi(argv[1]);
    size_t sz = N * N * sizeof(dtype);

    vector<dtype> hA(N*N), hB(N*N), hC(N*N);
    mt19937_64 rng(0);
    uniform_real_distribution<dtype> dist(0.0,1.0);
    for(int i=0;i<N*N;++i){ hA[i]=dist(rng); hB[i]=dist(rng); }

    dtype *dA, *dB, *dC;
    cudaMalloc(&dA, sz);
    cudaMalloc(&dB, sz);
    cudaMalloc(&dC, sz);
    cudaMemcpy(dA, hA.data(), sz, cudaMemcpyHostToDevice);
    cudaMemcpy(dB, hB.data(), sz, cudaMemcpyHostToDevice);

    dim3 block(16,16);
    dim3 grid((N+15)/16, (N+15)/16);
    cudaDeviceSynchronize();
    auto t0 = chrono::high_resolution_clock::now();
    kern_dgemm<<<grid, block>>>(dA, dB, dC, N);
    cudaDeviceSynchronize();
    auto t1 = chrono::high_resolution_clock::now();

    cudaMemcpy(hC.data(), dC, sz, cudaMemcpyDeviceToHost);
    cudaFree(dA); cudaFree(dB); cudaFree(dC);

    chrono::duration<double> dt = t1 - t0;
    cout<<"cuda, "<<N<<", "<<dt.count()<<"\n";
    return 0;
}
