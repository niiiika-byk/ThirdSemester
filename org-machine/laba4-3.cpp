//использованием библиотеки стандарта MPI
#include <mpi.h> //Intel TBB
#include <iostream>
#include <vector>
#include <random>
#include <chrono>

using dtype = double;

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    if(argc<2){ if(rank==0) std::cerr<<"Usage: "<<argv[0]<<" N\n"; MPI_Finalize(); return 1; }
    int N = std::stoi(argv[1]);
    int per = N / size;
    int start = rank * per;
    int end   = (rank == size-1 ? N : start + per);

    std::vector<dtype> A(N*N), B(N*N), C(N*N,0);
    if(rank==0) {
        std::mt19937_64 rng(0);
        std::uniform_real_distribution<dtype> dist(0.0,1.0);
        for(int i=0;i<N*N;++i){ A[i]=dist(rng); B[i]=dist(rng); }
    }
    MPI_Bcast(A.data(), N*N, MPI_DOUBLE, 0, MPI_COMM_WORLD);
    MPI_Bcast(B.data(), N*N, MPI_DOUBLE, 0, MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    auto t0 = std::chrono::high_resolution_clock::now();
    for(int i=start;i<end;++i)
        for(int j=0;j<N;++j){
            dtype sum=0;
            for(int k=0;k<N;++k)
                sum+=A[i*N+k]*B[k*N+j];
            C[i*N+j]=sum;
        }
    MPI_Barrier(MPI_COMM_WORLD);
    auto t1 = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> dt = t1 - t0;
    double t_local = dt.count();
    double t_max;
    MPI_Reduce(&t_local, &t_max, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    if(rank==0)
        std::cout<<"mpi, "<<N<<", "<<size<<", "<<t_max<<"\n";

    MPI_Finalize();
    return 0;
}
