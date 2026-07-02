import hashlib
import os
import time
from multiprocessing import Process, Queue, cpu_count
import matplotlib.pyplot as *__*

# ─── 設定 ────────────────────────────────────────────
MESSAGE = "Hello, blockchain!"
USE_MULTIPROCESS = False  # Trueにすると並列処理
MAX_CORES = cpu_count()
N_WORKERS = max(2, MAX_CORES - 4) if USE_MULTIPROCESS else 1

# ─── 共通の計算ロジック ─────────────────────────────
def find_nonce(start_nonce: int, step: int, stop_check, result_callback, message, prefix):
    nonce = start_nonce
    tried = 0
    while True:
        if stop_check():
            return
        h = hashlib.sha256(f"{message}{nonce}".encode()).hexdigest()
        if h.startswith(prefix):
            result_callback(nonce, tried + 1, h)
            return
        nonce += step
        tried += 1

def worker(start_nonce: int, step: int, out_q: Queue, message: str, prefix: str) -> None:
    def stop_check():
        return not out_q.empty()

    def result_callback(nonce, tried, h):
        out_q.put((nonce, tried, h))

    find_nonce(start_nonce, step, stop_check, result_callback, message, prefix)

if __name__ == "__main__":
    print(f"🚀 Mode: {'Multi-process' if USE_MULTIPROCESS else 'Single process'}")
    print(f"⏩ 使用コア数: {N_WORKERS} / 最大: {MAX_CORES}\n")

    difficulties = range(1, 9)
    times = []
    trials = []

    for difficulty in difficulties:
        prefix = "0" * difficulty
        print(f"🎯 難易度 {difficulty} → prefix = '{prefix}'")

        start = time.time()

        if USE_MULTIPROCESS:
            result_q: Queue = Queue()

            procs = [
                Process(
                    target=worker,
                    args=(i, N_WORKERS, result_q, MESSAGE, prefix),
                    daemon=True,
                )
                for i in range(N_WORKERS)
            ]
            for p in procs:
                p.start()

            nonce, tried, h = result_q.get()
            elapsed = time.time() - start

            for p in procs:
                p.terminate()
                p.join()

            total_tried = tried * N_WORKERS

        else:
            result_holder = {}

            def stop_check():
                return bool(result_holder)

            def result_callback(nonce, tried, h):
                result_holder["nonce"] = nonce
                result_holder["tried"] = tried
                result_holder["hash"] = h

            find_nonce(0, 1, stop_check, result_callback, MESSAGE, prefix)
            elapsed = time.time() - start

            nonce = result_holder["nonce"]
            tried = result_holder["tried"]
            h = result_holder["hash"]
            total_tried = tried

        # 結果表示
        print("✅ FOUND!")
        print(f"🔢 nonce        = {nonce}")
        print(f"🔑 hash         = {h}")
        print(f"🧮 total trials = {total_tried:,}")
        print(f"⏱️ elapsed      = {elapsed:.2f} s\n")

        # 時間記録
        times.append(elapsed)
        trials.append(total_tried)

    plt.figure(figsize=(8, 5))
    plt.plot(difficulties, times, marker="o")
    plt.xlabel("*__*")
    plt.ylabel("*__*")
    plt.grid(True)
    plt.xticks(difficulties)
    plt.tight_layout()
    plt.savefig("nonce.png")

    plt.figure(figsize=(8, 5))
    plt.plot(difficulties, trials, marker='s', linestyle='-', linewidth=2)
    plt.xlabel("*__*")
    plt.ylabel("*__*")
    plt.xticks(difficulties)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("trials.png")