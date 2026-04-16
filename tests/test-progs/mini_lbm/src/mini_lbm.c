// mini_lbm.c - fast, lbm-ish FP + memory streaming benchmark (single file)
//
// Build (via Makefile.x86 in this directory):
//   make -f Makefile.x86
//
// Run:
//   ./mini_lbm -n 16384 -i 4 -q
//
// Options:
//   -n <cells>     number of cells (default: 262144)
//   -i <iters>     iterations (default: 200)
//   -s <seed>      seed (default: 1)
//   -q             quiet (no per-iter printing)

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static uint32_t xorshift32(uint32_t *state)
{
    uint32_t x = *state;
    x ^= x << 13;
    x ^= x >> 17;
    x ^= x << 5;
    *state = x;
    return x;
}

static double now_sec(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + 1e-9 * (double)ts.tv_nsec;
}

static void usage(const char *argv0)
{
    fprintf(stderr,
        "Usage: %s [-n cells] [-i iters] [-s seed] [-q]\n"
        "  -n <cells>  number of cells (default 262144)\n"
        "  -i <iters>  iterations (default 200)\n"
        "  -s <seed>   seed (default 1)\n"
        "  -q          quiet\n",
        argv0);
}

int main(int argc, char **argv)
{
    size_t n = 262144;
    int iters = 200;
    uint32_t seed = 1;
    int quiet = 0;

    for (int a = 1; a < argc; a++) {
        if (!strcmp(argv[a], "-n") && a + 1 < argc) {
            n = (size_t)strtoull(argv[++a], NULL, 0);
        } else if (!strcmp(argv[a], "-i") && a + 1 < argc) {
            iters = (int)strtol(argv[++a], NULL, 0);
        } else if (!strcmp(argv[a], "-s") && a + 1 < argc) {
            seed = (uint32_t)strtoul(argv[++a], NULL, 0);
        } else if (!strcmp(argv[a], "-q")) {
            quiet = 1;
        } else {
            usage(argv[0]);
            return 2;
        }
    }

    if (n < 32 || iters < 1) {
        fprintf(stderr, "Invalid args.\n");
        return 2;
    }

    const double omega = 1.7;
    const double inv_cs2 = 3.0; // 1 / (1/3)

    // D3Q19 directions
    static const int8_t cx[19] = { 0,  1,-1, 0, 0, 0, 0,  1,-1, 1,-1,  1,-1, 1,-1, 0, 0, 0, 0 };
    static const int8_t cy[19] = { 0,  0, 0, 1,-1, 0, 0,  1, 1,-1,-1,  0, 0, 0, 0, 1,-1, 1,-1 };
    static const int8_t cz[19] = { 0,  0, 0, 0, 0, 1,-1,  0, 0, 0, 0,  1, 1,-1,-1, 1, 1,-1,-1 };
    static const double w[19] = {
        1.0/3.0,
        1.0/18.0,1.0/18.0,1.0/18.0,1.0/18.0,1.0/18.0,1.0/18.0,
        1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0,1.0/36.0
    };

    // Skinny 3D domain mapping to keep it simple
    const int X = 128;
    const int Y = 64;
    const int Z = (int)((n + (size_t)(X * Y) - 1) / (size_t)(X * Y));
    const size_t cells = (size_t)X * (size_t)Y * (size_t)Z;
    if (cells < n)
        n = cells;

    const size_t Q = 19;

    double *f0 = (double *)aligned_alloc(64, n * Q * sizeof(double));
    double *f1 = (double *)aligned_alloc(64, n * Q * sizeof(double));
    uint8_t *solid = (uint8_t *)aligned_alloc(64, n * sizeof(uint8_t));
    if (!f0 || !f1 || !solid) {
        fprintf(stderr, "alloc failed\n");
        return 1;
    }

    // init
    for (size_t i = 0; i < n; i++) {
        uint32_t r = xorshift32(&seed);
        solid[i] = (uint8_t)(((r >> 0) & 255u) < 12u); // ~5% obstacles
        double rho = 1.0 + 0.01 * ((int)((r >> 8) & 255u) - 128) / 128.0;
        double ux = 0.02 * ((int)((r >> 16) & 255u) - 128) / 128.0;
        double uy = 0.02 * ((int)((r >> 24) & 255u) - 128) / 128.0;
        double uz = 0.01 * ((int)(xorshift32(&seed) & 255u) - 128) / 128.0;

        const double u2 = ux * ux + uy * uy + uz * uz;
        for (size_t q = 0; q < Q; q++) {
            const double cu = (double)cx[q] * ux + (double)cy[q] * uy + (double)cz[q] * uz;
            const double feq = w[q] * rho * (1.0 + inv_cs2 * cu + 0.5 * inv_cs2 * inv_cs2 * cu * cu - 0.5 * inv_cs2 * u2);
            f0[i * Q + q] = feq;
            f1[i * Q + q] = 0.0;
        }
    }

    double t0 = now_sec();
    double checksum = 0.0;

    for (int it = 0; it < iters; it++) {
        for (size_t i = 0; i < n; i++) {
            const size_t base = i * Q;

            if (solid[i]) {
                for (size_t q = 0; q < Q; q++)
                    f1[base + q] = f0[base + (Q - 1 - q)];
                continue;
            }

            double rho = 0.0, ux = 0.0, uy = 0.0, uz = 0.0;
            for (size_t q = 0; q < Q; q++) {
                const double fq = f0[base + q];
                rho += fq;
                ux += fq * (double)cx[q];
                uy += fq * (double)cy[q];
                uz += fq * (double)cz[q];
            }

            const double inv_rho = 1.0 / (rho + 1e-30);
            ux *= inv_rho;
            uy *= inv_rho;
            uz *= inv_rho;

            const double jitter = (double)((i ^ (size_t)it) & 15u) * 1e-6;
            ux += jitter;
            uy -= jitter * 0.5;
            uz += jitter * 0.25;

            const double u2 = ux * ux + uy * uy + uz * uz;

            const int x = (int)(i % (size_t)X);
            const int y = (int)((i / (size_t)X) % (size_t)Y);
            const int z = (int)(i / (size_t)(X * Y));

            for (size_t q = 0; q < Q; q++) {
                const double cu = (double)cx[q] * ux + (double)cy[q] * uy + (double)cz[q] * uz;
                const double feq = w[q] * rho * (1.0 + inv_cs2 * cu + 0.5 * inv_cs2 * inv_cs2 * cu * cu - 0.5 * inv_cs2 * u2);
                const double fout = f0[base + q] + omega * (feq - f0[base + q]);

                int nx = x + (int)cx[q];
                int ny = y + (int)cy[q];
                int nz = z + (int)cz[q];
                if (nx < 0) nx += X; else if (nx >= X) nx -= X;
                if (ny < 0) ny += Y; else if (ny >= Y) ny -= Y;
                if (nz < 0) nz += Z; else if (nz >= Z) nz -= Z;

                const size_t ni = (size_t)nx + (size_t)X * ((size_t)ny + (size_t)Y * (size_t)nz);
                if (ni < n)
                    f1[ni * Q + q] = fout;
                else
                    f1[base + q] = fout;
            }
        }

        double *tmp = f0;
        f0 = f1;
        f1 = tmp;

        double partial = 0.0;
        for (size_t i = 0; i < n; i += 97)
            partial += f0[i * Q + (size_t)((i + (size_t)it) % Q)];
        checksum += partial;

        if (!quiet && (it % 25 == 0 || it == iters - 1))
            fprintf(stdout, "iter %d/%d  checksum=%.6f\n", it + 1, iters, checksum);
    }

    double t1 = now_sec();
    fprintf(stdout, "done: n=%zu iters=%d time=%.3fs checksum=%.6f\n", n, iters, (t1 - t0), checksum);

    free(f0);
    free(f1);
    free(solid);
    return 0;
}

