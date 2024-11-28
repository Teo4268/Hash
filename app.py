import json
import struct
import time
import socket
import threading
import ctypes
from stratum import StratumClient

# Load the MinotaurX hash function from the shared C++ library
minotaurx = ctypes.CDLL('./minotaurx_hash.so')  # Chỉ ra đường dẫn đến thư viện đã build từ C++

# Define your mining pool details
POOL_HOST = 'minotaurx.sea.mine.zpool.ca'  # Thay thế với pool của bạn
POOL_PORT = 7019  # Port của pool
WORKER_NAME = 'R9uHDn9XXqPAe2TLsEmVoNrokmWsHREV2Q'  # Wallet address của bạn
PASSWORD = 'c=RVN'  # Password (hoặc thông số cho cổng RVN)

# Function to handle job received from the pool and mine using MinotaurX
def mine_thread(worker_name, client):
    def on_job(job):
        print(f"Thread {worker_name} received job:", job)
        job_id = job['job_id']
        target = int(job['target'], 16)  # Chuyển target từ hex sang int
        header = bytes.fromhex(job['header'])  # Đọc header từ hex
        extra_nonce = job['extra_nonce']  # Extra nonce từ pool

        # Start mining loop to find the correct hash
        nonce = 0  # Khởi tạo nonce từ 0
        while True:
            # Tạo header mới kết hợp với nonce
            new_header = header + struct.pack('<I', nonce)  # Append nonce vào header

            # Call the MinotaurX hash function (you must pass the right arguments)
            result = minotaurx.hash_function(new_header)  # Thay thế bằng tên hàm hash thực tế trong thư viện của bạn

            # Kiểm tra xem kết quả hash có thỏa mãn target không
            if int(result, 16) <= target:
                # Nếu hash hợp lệ, gửi kết quả về pool
                client.submit_work(job_id, nonce, result)
                print(f"Thread {worker_name}: Solution found and submitted: {result}")
                break
            
            # Tăng nonce để thử nghiệm hash khác
            nonce += 1

        time.sleep(1)  # Chờ 1 giây trước khi nhận job mới

    # Đặt handler cho job nhận từ pool
    client.on_job(on_job)

    # Bắt đầu mining
    client.start_mining()

# Function to start multiple mining threads
def start_mining_threads(num_threads):
    threads = []
    
    # Khởi tạo các threads
    for i in range(num_threads):
        worker_name = f"{WORKER_NAME}_thread_{i+1}"  # Tạo tên worker cho mỗi thread
        client = StratumClient(POOL_HOST, POOL_PORT, worker_name, PASSWORD)
        client.connect(keepalive=True)  # Giữ kết nối hoạt động liên tục
        
        # Tạo và khởi động thread
        thread = threading.Thread(target=mine_thread, args=(worker_name, client))
        threads.append(thread)
        thread.start()

    # Đợi cho tất cả các threads hoàn thành
    for thread in threads:
        thread.join()

# Main function to start the mining process with multiple threads
if __name__ == '__main__':
    num_threads = 2  # Chỉnh số lượng thread ở đây
    start_mining_threads(num_threads)
