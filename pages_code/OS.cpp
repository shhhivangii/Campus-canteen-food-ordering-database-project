/*
 * CPU Task Scheduler Simulator (single-core)
 * ------------------------------------------
 * Algorithms : FCFS, SJF (non-preemptive), SRTF (preemptive SJF),
 *              Priority (non-preemptive / preemptive), Round Robin
 * Outputs    : Gantt chart, CT / TAT / WT / RT per process, averages,
 *              CPU utilisation, throughput, context switches,
 *              side-by-side comparison of all algorithms.
 *
 * Conventions:
 *   - Lower priority number = higher priority.
 *   - Ties are broken by arrival time, then by PID.
 *   - Time is in integer units; CPU utilisation is measured from the
 *     first arrival to the last completion.
 *
 * Compile : g++ -std=c++17 -O2 -Wall -o scheduler scheduler.cpp
 * Run     : ./scheduler
 */

#include <algorithm>
#include <climits>
#include <functional>
#include <iomanip>
#include <iostream>
#include <limits>
#include <queue>
#include <sstream>
#include <string>
#include <vector>

using namespace std;

// ----------------------------------------------------------------------
// Data structures
// ----------------------------------------------------------------------
struct Process {
    int pid;
    int at;          // arrival time
    int bt;          // burst time
    int pr;          // priority (lower = higher priority)
    int rem;         // remaining burst time
    int start = -1;  // first time the process got the CPU
    int ct = 0;      // completion time
    int tat() const { return ct - at; }
    int wt() const { return tat() - bt; }
    int rt() const { return start - at; }
};

struct Segment {
    int pid;  // -1 means CPU idle
    int s, e;
};

struct Result {
    string name;
    vector<Process> procs;
    vector<Segment> gantt;
    int firstArrival = 0;
    int endTime = 0;

    int busyTime() const {
        int b = 0;
        for (auto &g : gantt) if (g.pid != -1) b += g.e - g.s;
        return b;
    }
    int contextSwitches() const {
        int cs = 0, last = -2;
        for (auto &g : gantt) {
            if (g.pid == -1) continue;
            if (last != -2 && g.pid != last) cs++;
            last = g.pid;
        }
        return cs;
    }
    double cpuUtil() const {
        int span = endTime - firstArrival;
        return span > 0 ? 100.0 * busyTime() / span : 0.0;
    }
    double avg(function<int(const Process &)> f) const {
        double sum = 0;
        for (auto &p : procs) sum += f(p);
        return procs.empty() ? 0 : sum / procs.size();
    }
    double throughput() const {
        int span = endTime - firstArrival;
        return span > 0 ? (double)procs.size() / span : 0.0;
    }
};

// ----------------------------------------------------------------------
// Helpers
// ----------------------------------------------------------------------
static void addSeg(vector<Segment> &g, int pid, int s, int e) {
    if (!g.empty() && g.back().pid == pid && g.back().e == s)
        g.back().e = e;  // merge contiguous slices of the same process
    else
        g.push_back({pid, s, e});
}

static int earliestArrival(const vector<Process> &p) {
    int m = INT_MAX;
    for (auto &x : p) m = min(m, x.at);
    return m;
}

static Result finish(const string &name, vector<Process> p, vector<Segment> g, int first) {
    Result r;
    r.name = name;
    r.procs = move(p);
    r.gantt = move(g);
    r.firstArrival = first;
    r.endTime = r.gantt.empty() ? first : r.gantt.back().e;
    sort(r.procs.begin(), r.procs.end(),
         [](const Process &a, const Process &b) { return a.pid < b.pid; });
    return r;
}

// ----------------------------------------------------------------------
// Scheduling algorithms
// ----------------------------------------------------------------------
using KeyFn = function<int(const Process &)>;

// Picks, among arrived & unfinished processes, the smallest (key, at, pid).
static int pickBest(const vector<Process> &p, int t, const KeyFn &key) {
    int best = -1;
    for (int i = 0; i < (int)p.size(); i++) {
        if (p[i].at > t || p[i].rem <= 0) continue;
        if (best == -1) { best = i; continue; }
        auto a = make_tuple(key(p[i]), p[i].at, p[i].pid);
        auto b = make_tuple(key(p[best]), p[best].at, p[best].pid);
        if (a < b) best = i;
    }
    return best;
}

// Non-preemptive: FCFS (key = arrival), SJF (key = burst), Priority (key = pr)
static Result runNonPreemptive(const string &name, vector<Process> p, KeyFn key) {
    vector<Segment> g;
    int n = p.size(), done = 0;
    int first = earliestArrival(p), t = first;
    while (done < n) {
        int i = pickBest(p, t, key);
        if (i == -1) {  // CPU idle until next arrival
            int next = INT_MAX;
            for (auto &x : p) if (x.rem > 0) next = min(next, x.at);
            addSeg(g, -1, t, next);
            t = next;
            continue;
        }
        p[i].start = t;
        addSeg(g, p[i].pid, t, t + p[i].bt);
        t += p[i].bt;
        p[i].rem = 0;
        p[i].ct = t;
        done++;
    }
    return finish(name, p, g, first);
}

// Preemptive: SRTF (key = remaining) and preemptive Priority (key = pr).
// Decision is re-evaluated at every time unit.
static Result runPreemptive(const string &name, vector<Process> p, KeyFn key) {
    vector<Segment> g;
    int n = p.size(), done = 0;
    int first = earliestArrival(p), t = first;
    while (done < n) {
        int i = pickBest(p, t, key);
        if (i == -1) {
            addSeg(g, -1, t, t + 1);
            t++;
            continue;
        }
        if (p[i].start == -1) p[i].start = t;
        addSeg(g, p[i].pid, t, t + 1);
        p[i].rem--;
        t++;
        if (p[i].rem == 0) { p[i].ct = t; done++; }
    }
    return finish(name, p, g, first);
}

// Round Robin with a fixed time quantum.
static Result runRoundRobin(vector<Process> p, int quantum) {
    vector<Segment> g;
    int n = p.size(), done = 0;
    int first = earliestArrival(p), t = first;

    vector<int> order(n);
    for (int i = 0; i < n; i++) order[i] = i;
    sort(order.begin(), order.end(), [&](int a, int b) {
        return make_pair(p[a].at, p[a].pid) < make_pair(p[b].at, p[b].pid);
    });

    queue<int> rq;
    int nextIdx = 0;
    auto admit = [&](int now) {
        while (nextIdx < n && p[order[nextIdx]].at <= now) rq.push(order[nextIdx++]);
    };

    admit(t);
    while (done < n) {
        if (rq.empty()) {  // idle gap
            int nextAt = p[order[nextIdx]].at;
            addSeg(g, -1, t, nextAt);
            t = nextAt;
            admit(t);
            continue;
        }
        int i = rq.front(); rq.pop();
        if (p[i].start == -1) p[i].start = t;
        int run = min(quantum, p[i].rem);
        addSeg(g, p[i].pid, t, t + run);
        t += run;
        p[i].rem -= run;
        admit(t);                       // new arrivals queue before the preempted process
        if (p[i].rem > 0) rq.push(i);
        else { p[i].ct = t; done++; }
    }
    return finish("Round Robin (q=" + to_string(quantum) + ")", p, g, first);
}

// ----------------------------------------------------------------------
// Output
// ----------------------------------------------------------------------
static string label(int pid) { return pid == -1 ? "IDLE" : "P" + to_string(pid); }

static void printGantt(const Result &r) {
    string bar = "|", nums;
    nums = to_string(r.gantt.front().s);
    size_t pos = 1;  // column of the current boundary

    for (auto &sg : r.gantt) {
        string lab = label(sg.pid);
        size_t width = max<size_t>({lab.size() + 2, (size_t)(sg.e - sg.s), to_string(sg.e).size() + 2, (size_t)4});
        size_t left = (width - lab.size()) / 2;
        bar += string(left, ' ') + lab + string(width - left - lab.size(), ' ') + "|";
        pos += width + 1;
        string n = to_string(sg.e);
        // place end-time so it begins at the boundary column
        size_t target = pos - 1;
        if (nums.size() < target) nums += string(target - nums.size(), ' ');
        else nums += " ";
        nums += n;
    }
    string line(bar.size(), '-');
    cout << "\nGantt Chart:\n " << line << "\n " << bar << "\n " << line << "\n " << nums << "\n";
}

static void printTable(const Result &r) {
    cout << "\n" << left << setw(6) << "PID" << setw(6) << "AT" << setw(6) << "BT"
         << setw(6) << "PR" << setw(6) << "CT" << setw(6) << "TAT"
         << setw(6) << "WT" << setw(6) << "RT" << "\n"
         << string(48, '-') << "\n";
    for (auto &p : r.procs)
        cout << left << setw(6) << ("P" + to_string(p.pid)) << setw(6) << p.at << setw(6) << p.bt
             << setw(6) << p.pr << setw(6) << p.ct << setw(6) << p.tat()
             << setw(6) << p.wt() << setw(6) << p.rt() << "\n";
    cout << string(48, '-') << "\n" << fixed << setprecision(2)
         << "Average Turnaround Time : " << r.avg([](const Process &p) { return p.tat(); }) << "\n"
         << "Average Waiting Time    : " << r.avg([](const Process &p) { return p.wt(); }) << "\n"
         << "Average Response Time   : " << r.avg([](const Process &p) { return p.rt(); }) << "\n"
         << "CPU Utilisation         : " << r.cpuUtil() << " %\n"
         << "Throughput              : " << r.throughput() << " processes/unit\n"
         << "Context Switches        : " << r.contextSwitches() << "\n";
}

static void report(const Result &r) {
    cout << "\n==================== " << r.name << " ====================";
    printGantt(r);
    printTable(r);
}

static void printComparison(const vector<Result> &rs) {
    cout << "\n=========================== ALGORITHM COMPARISON ===========================\n"
         << left << setw(28) << "Algorithm" << setw(9) << "Avg TAT" << setw(9) << "Avg WT"
         << setw(9) << "Avg RT" << setw(10) << "CPU %" << setw(8) << "Ctx Sw" << "\n"
         << string(73, '-') << "\n" << fixed << setprecision(2);
    for (auto &r : rs)
        cout << left << setw(28) << r.name
             << setw(9) << r.avg([](const Process &p) { return p.tat(); })
             << setw(9) << r.avg([](const Process &p) { return p.wt(); })
             << setw(9) << r.avg([](const Process &p) { return p.rt(); })
             << setw(10) << r.cpuUtil() << setw(8) << r.contextSwitches() << "\n";

    auto best = [&](function<double(const Result &)> f) {
        return min_element(rs.begin(), rs.end(),
                           [&](const Result &a, const Result &b) { return f(a) < f(b); })->name;
    };
    cout << string(73, '-') << "\n"
         << "Best Avg Waiting Time    : " << best([](const Result &r) { return r.avg([](const Process &p) { return p.wt(); }); }) << "\n"
         << "Best Avg Turnaround Time : " << best([](const Result &r) { return r.avg([](const Process &p) { return p.tat(); }); }) << "\n"
         << "Best Avg Response Time   : " << best([](const Result &r) { return r.avg([](const Process &p) { return p.rt(); }); }) << "\n"
         << "Fewest Context Switches  : " << best([](const Result &r) { return (double)r.contextSwitches(); }) << "\n";
}

// ----------------------------------------------------------------------
// Input handling
// ----------------------------------------------------------------------
static int readInt(const string &prompt, int lo, int hi = INT_MAX) {
    int v;
    while (true) {
        cout << prompt;
        if (cin >> v && v >= lo && v <= hi) return v;
        if (cin.eof()) { cout << "\nInput closed. Exiting.\n"; exit(0); }
        cin.clear();
        cin.ignore(numeric_limits<streamsize>::max(), '\n');
        cout << "  Invalid input. Enter a number";
        cout << " >= " << lo;
        if (hi != INT_MAX) cout << " and <= " << hi;
        cout << ".\n";
    }
}

static vector<Process> sampleProcesses() {
    vector<Process> p = {
        {1, 0, 8, 3, 8}, {2, 1, 4, 1, 4}, {3, 2, 9, 4, 9},
        {4, 3, 5, 2, 5}, {5, 35, 3, 1, 3}  // P5 arrives late -> shows CPU idle time
    };
    return p;
}

static vector<Process> inputProcesses() {
    int n = readInt("Number of processes (1-50): ", 1, 50);
    vector<Process> p;
    for (int i = 1; i <= n; i++) {
        cout << "--- Process P" << i << " ---\n";
        Process x;
        x.pid = i;
        x.at = readInt("  Arrival time : ", 0);
        x.bt = readInt("  Burst time   : ", 1);
        x.pr = readInt("  Priority (lower = higher): ", 0);
        x.rem = x.bt;
        p.push_back(x);
    }
    return p;
}

static void showInput(const vector<Process> &p) {
    cout << "\nCurrent processes:\n" << left << setw(6) << "PID" << setw(6) << "AT"
         << setw(6) << "BT" << setw(6) << "PR" << "\n" << string(24, '-') << "\n";
    for (auto &x : p)
        cout << left << setw(6) << ("P" + to_string(x.pid)) << setw(6) << x.at
             << setw(6) << x.bt << setw(6) << x.pr << "\n";
}

// ----------------------------------------------------------------------
// Algorithm dispatch
// ----------------------------------------------------------------------
static Result fcfs(const vector<Process> &p) {
    return runNonPreemptive("FCFS", p, [](const Process &x) { return x.at; });
}
static Result sjf(const vector<Process> &p) {
    return runNonPreemptive("SJF (Non-preemptive)", p, [](const Process &x) { return x.bt; });
}
static Result srtf(const vector<Process> &p) {
    return runPreemptive("SRTF (Preemptive SJF)", p, [](const Process &x) { return x.rem; });
}
static Result priorityNP(const vector<Process> &p) {
    return runNonPreemptive("Priority (Non-preemptive)", p, [](const Process &x) { return x.pr; });
}
static Result priorityP(const vector<Process> &p) {
    return runPreemptive("Priority (Preemptive)", p, [](const Process &x) { return x.pr; });
}

int main() {
    cout << "=====================================================\n"
         << "      CPU TASK SCHEDULER SIMULATOR (Single Core)\n"
         << "=====================================================\n";

    vector<Process> procs;
    while (true) {
        cout << "\n--------------------- MENU ---------------------\n"
             << " 1. Enter processes manually\n"
             << " 2. Load sample processes\n"
             << " 3. Show current processes\n"
             << " 4. Run FCFS\n"
             << " 5. Run SJF (Non-preemptive)\n"
             << " 6. Run SRTF (Preemptive SJF)\n"
             << " 7. Run Priority Scheduling\n"
             << " 8. Run Round Robin\n"
             << " 9. Compare ALL algorithms\n"
             << " 0. Exit\n";
        int ch = readInt("Choice: ", 0, 9);

        if (ch == 0) { cout << "Goodbye!\n"; break; }
        if (ch == 1) { procs = inputProcesses(); continue; }
        if (ch == 2) { procs = sampleProcesses(); showInput(procs); continue; }
        if (procs.empty()) { cout << "\nNo processes loaded. Use option 1 or 2 first.\n"; continue; }
        if (ch == 3) { showInput(procs); continue; }

        switch (ch) {
            case 4: report(fcfs(procs)); break;
            case 5: report(sjf(procs)); break;
            case 6: report(srtf(procs)); break;
            case 7: {
                int mode = readInt("  1 = Non-preemptive, 2 = Preemptive: ", 1, 2);
                report(mode == 1 ? priorityNP(procs) : priorityP(procs));
                break;
            }
            case 8: {
                int q = readInt("  Time quantum: ", 1);
                report(runRoundRobin(procs, q));
                break;
            }
            case 9: {
                int q = readInt("  Time quantum for Round Robin: ", 1);
                vector<Result> all = {fcfs(procs), sjf(procs), srtf(procs),
                                      priorityNP(procs), priorityP(procs),
                                      runRoundRobin(procs, q)};
                for (auto &r : all) report(r);
                printComparison(all);
                break;
            }
        }
    }
    return 0;
