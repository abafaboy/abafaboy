// Growth rate of memory-m walks on Z^2 (no loop of length <= m), via a
// symmetry-reduced automaton and power iteration.
//
// State: set of past sites relative to the endpoint, each with remaining
// lifetime r (site may not be entered within the next r steps). Entries with
// L1 distance > r are dropped; r is lowered to the parity of the distance.
//
// build: g++ -O3 -march=native -fopenmp -o mem mem.cpp
#include <bits/stdc++.h>
using namespace std;

typedef uint32_t E;  // entry: x(8 bits, +64) | y(8 bits, +64) | r(8 bits)
static inline E pack(int x, int y, int r) { return (uint32_t(x + 64) << 16) | (uint32_t(y + 64) << 8) | uint32_t(r); }
static inline int ex(E e) { return int((e >> 16) & 255) - 64; }
static inline int ey(E e) { return int((e >> 8) & 255) - 64; }
static inline int er(E e) { return int(e & 255); }

int M, TRAP = 0;

struct VecHash {
    size_t operator()(const vector<E>& v) const {
        uint64_t h = 1469598103934665603ULL;
        for (E e : v) { h ^= e; h *= 1099511628211ULL; h ^= h >> 29; }
        return h;
    }
};

static inline void sym(int k, int x, int y, int& X, int& Y) {
    switch (k) {
        case 0: X = x; Y = y; break;   case 1: X = -x; Y = y; break;
        case 2: X = x; Y = -y; break;  case 3: X = -x; Y = -y; break;
        case 4: X = y; Y = x; break;   case 5: X = -y; Y = x; break;
        case 6: X = y; Y = -x; break;  default: X = -y; Y = -x; break;
    }
}

vector<E> canon(const vector<E>& s) {
    vector<E> best, cur;
    for (int k = 0; k < 8; k++) {
        cur.clear();
        for (E e : s) { int X, Y; sym(k, ex(e), ey(e), X, Y); cur.push_back(pack(X, Y, er(e))); }
        sort(cur.begin(), cur.end());
        if (k == 0 || cur < best) best = cur;
    }
    return best;
}

int main(int argc, char** argv) {
    M = atoi(argv[1]);
    TRAP = argc > 2 ? atoi(argv[2]) : 0;
    int iters = 20000;
    const int DX[4] = {1, -1, 0, 0}, DY[4] = {0, 0, 1, -1};
    unordered_map<vector<E>, uint32_t, VecHash> idx;
    vector<vector<E>> states;
    vector<array<int32_t, 4>> tr;
    vector<E> st0;
    idx[st0] = 0; states.push_back(st0);
    auto t0 = chrono::steady_clock::now();
    for (size_t q = 0; q < states.size(); q++) {
        array<int32_t, 4> row = {-1, -1, -1, -1};
        const vector<E> S = states[q];
        for (int d = 0; d < 4; d++) {
            int sx = DX[d], sy = DY[d];
            bool bad = false;
            for (E e : S) if (ex(e) == sx && ey(e) == sy && er(e) >= 1) { bad = true; break; }
            if (bad) continue;
            vector<E> nw;
            auto add = [&](int x, int y, int r) {
                int dist = abs(x) + abs(y);
                if (dist <= r && r >= 1) { r -= (r - dist) & 1; nw.push_back(pack(x, y, r)); }
            };
            for (E e : S) add(ex(e) - sx, ey(e) - sy, er(e) - 1);
            add(-sx, -sy, M - 1);
            if (TRAP) {
                // remembered sites (incl. dropped-but-true ones we still have: use S shifted + old endpoint)
                // use ALL sites known in S (true visited sites), not only the kept ones
                int B = 2;
                vector<pair<int,int>> occ;
                for (E e : S) { int x = ex(e) - sx, y = ey(e) - sy; occ.push_back({x, y}); B = max(B, max(abs(x), abs(y)) + 2); }
                occ.push_back({-sx, -sy});
                int W = 2 * B + 1;
                static vector<uint8_t> grid; grid.assign(W * W, 0);
                for (auto& p : occ) grid[(p.second + B) * W + (p.first + B)] = 1;
                static vector<int> stk; stk.clear();
                stk.push_back(B * W + B); grid[B * W + B] = 2;
                bool esc = false;
                while (!stk.empty() && !esc) {
                    int c = stk.back(); stk.pop_back();
                    int cx = c % W, cy = c / W;
                    if (cx == 0 || cy == 0 || cx == W - 1 || cy == W - 1) { esc = true; break; }
                    const int nb[4] = {c + 1, c - 1, c + W, c - W};
                    for (int k = 0; k < 4; k++) if (grid[nb[k]] == 0) { grid[nb[k]] = 2; stk.push_back(nb[k]); }
                }
                if (!esc) continue;   // sealed in a pocket: walk cannot be endless
            }
            vector<E> c = canon(nw);
            auto it = idx.find(c);
            uint32_t id;
            if (it == idx.end()) { id = states.size(); idx.emplace(c, id); states.push_back(c); }
            else id = it->second;
            row[d] = id;
        }
        tr.push_back(row);
        if ((q & 0xFFFFF) == 0 && q) fprintf(stderr, "  built %zu / %zu states\n", q, states.size());
    }
    size_t n = states.size();
    double tb = chrono::duration<double>(chrono::steady_clock::now() - t0).count();
    { unordered_map<vector<E>, uint32_t, VecHash>().swap(idx); vector<vector<E>>().swap(states); }
    // power iteration
    vector<double> v(n, 1.0), w(n);
    double lam = 0, lo = 0, hi = 0;
    for (int it = 0; it < iters; it++) {
        #pragma omp parallel for schedule(static)
        for (size_t i = 0; i < n; i++) {
            double s = 0;
            for (int d = 0; d < 4; d++) if (tr[i][d] >= 0) s += v[tr[i][d]];
            w[i] = s;
        }
        // Collatz-Wielandt bounds: min and max of (Av)_i / v_i
        double mn = 1e300, mx = 0, mxw = 0;
        #pragma omp parallel for reduction(min:mn) reduction(max:mx) reduction(max:mxw)
        for (size_t i = 0; i < n; i++) {
            double r = w[i] / v[i];
            if (r < mn) mn = r;
            if (r > mx) mx = r;
            if (w[i] > mxw) mxw = w[i];
        }
        lo = mn; hi = mx;
        #pragma omp parallel for
        for (size_t i = 0; i < n; i++) v[i] = w[i] / mxw;
        if (it % 200 == 0) fprintf(stderr, "  it %d  CW bounds [%.12f, %.12f]\n", it, lo, hi);
        if (hi - lo < 1e-11) break;
    }
    printf("trap=%d m=%d states=%zu  lambda in [%.12f, %.12f]  build %.1fs\n", TRAP, M, n, lo, hi, tb);
}
