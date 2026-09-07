#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

// The intentionally defective build rounds K down to a complete 8-element tile.
// It is a mutation fixture, not a claimed upstream GEMM Lab vulnerability.
#ifndef TAIL_MUTATION
#define TAIL_MUTATION 0
#endif

static int number(const char* s) {
    std::size_t end=0; const int v=std::stoi(s,&end);
    if (s[end]!='\0') throw std::invalid_argument("integer syntax");
    return v;
}

__attribute__((noinline))
void reference(const std::vector<double>& a, const std::vector<double>& b,
               std::vector<double>& c, int m, int n, int k) {
    for(int i=0;i<m;++i) for(int j=0;j<n;++j) {
        double sum=0;
        for(int q=0;q<k;++q) sum+=a[i*k+q]*b[q*n+j];
        c[i*n+j]=sum;
    }
}

__attribute__((noinline))
void optimized(const std::vector<double>& a, const std::vector<double>& b,
               std::vector<double>& c, int m, int n, int k) {
    std::fill(c.begin(),c.end(),0.0);
    const int limit=TAIL_MUTATION ? k/8*8 : k;
    // Contiguous B/C rows enable SIMD and avoid strided B loads in the inner loop.
    for(int i=0;i<m;++i) for(int q=0;q<limit;++q) {
        const double x=a[i*k+q];
        for(int j=0;j<n;++j) c[i*n+j]+=x*b[q*n+j];
    }
}

int main(int argc, char** argv) {
  try {
    if(argc==2 && std::string(argv[1])=="--version") {
        std::cout << "gemm-cpu-contract/1 " << (TAIL_MUTATION ? "mutant" : "fixed") << '\n'; return 0;
    }
    if(argc!=8) throw std::invalid_argument("usage: gemm MODE M N K REPS SEED generated|stdin");
    const std::string mode=argv[1], input=argv[7];
    const int m=number(argv[2]), n=number(argv[3]), k=number(argv[4]);
    const int reps=number(argv[5]), seed=number(argv[6]);
    if(mode!="reference" && mode!="optimized") throw std::invalid_argument("mode");
    if(input!="generated" && input!="stdin") throw std::invalid_argument("input mode");
    if(m<1||n<1||k<1||m>512||n>512||k>512||reps<1||reps>1000||seed<0||seed>100000)
        throw std::invalid_argument("dimension/repetition/seed limit");
    if(int64_t(m)*n*k*reps>500000000) throw std::invalid_argument("operation budget");
    std::vector<double> a(m*k), b(k*n), c(m*n);
    for(std::size_t i=0;i<a.size();++i) a[i]=(int((i*17+seed*13)%19)-9)/8.0;
    for(std::size_t i=0;i<b.size();++i) b[i]=(int((i*11+seed*7)%23)-11)/8.0;
    if(input=="stdin") {
        for(auto* v:{&a,&b}) for(double& x:*v)
            if(!(std::cin>>x)||!std::isfinite(x)||std::abs(x)>1000) throw std::invalid_argument("invalid matrix element");
        std::string extra; if(std::cin>>extra) throw std::invalid_argument("trailing input");
    }
    auto kernel=mode=="reference" ? reference : optimized;
    kernel(a,b,c,m,n,k); // Warmup and allocation are outside the kernel timer.
    std::vector<double> timings;
    for(int r=0;r<reps;++r) {
        auto t=std::chrono::steady_clock::now();
        kernel(a,b,c,m,n,k);
        auto end=std::chrono::steady_clock::now();
        timings.push_back(std::chrono::duration<double,std::micro>(end-t).count());
        // Every iteration's output remains observable, including under LTO.
        asm volatile("" : : "g"(c.data()) : "memory");
    }
    std::cout<<std::setprecision(17)<<"{\"protocol\":1,\"kernel_us\":[";
    for(std::size_t i=0;i<timings.size();++i) std::cout<<(i?",":"")<<timings[i];
    std::cout<<"],\"values\":[";
    for(std::size_t i=0;i<c.size();++i) std::cout<<(i?",":"")<<c[i];
    std::cout<<"]}\n";
    return 0;
  } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 2; }
}
