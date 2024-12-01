import socket
import threading
import random
import time

# Constants
SERVER_ADDRESS = ('localhost', 10000)
LOSS_PROBABILITY = 0.1  # Probability to simulate packet loss
TOTAL_PACKETS = 20
TIMEOUT = 2  # Timeout in seconds

class UDPSender:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.base = 0
        self.next_seq_num = 0
        self.lock = threading.Lock()
        self.timer = None

    def start_timer(self):
        if self.timer is None:
            self.timer = threading.Timer(TIMEOUT, self.timeout_handler)
            self.timer.start()

    def stop_timer(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None

    def timeout_handler(self):
        with self.lock:
            print(f"Timeout occurred. Resending packets from base: {self.base}")
            self.stop_timer()
            self.send_packets()

    def send_packets(self):
        with self.lock:
            while self.next_seq_num < self.base + 5 and self.next_seq_num < TOTAL_PACKETS:  # Window size = 5
                message = f"{self.next_seq_num}:Hello Receiver!"
                if random.random() > LOSS_PROBABILITY:  # Simulate packet loss
                    self.sock.sendto(message.encode(), SERVER_ADDRESS)
                    print(f"Sent: {message}")
                else:
                    print(f"Simulated loss: Packet {self.next_seq_num} not sent")
                if self.base == self.next_seq_num:
                    self.start_timer()
                self.next_seq_num += 1

    def receive_acks(self):
        while True:
            try:
                self.sock.settimeout(TIMEOUT)
                data, _ = self.sock.recvfrom(1024)
                ack_num = int(data.decode())
                print(f"Received ACK: {ack_num}")
                
                with self.lock:
                    if ack_num >= self.base:
                        self.base = ack_num + 1
                        self.stop_timer()
                        if self.base < TOTAL_PACKETS:
                            self.send_packets()
                        if self.base == TOTAL_PACKETS:
                            print("All packets acknowledged.")
                            break
            except socket.timeout:
                self.timeout_handler()
            except Exception as e:
                print(f"Error while receiving ACK: {e}")

    def run(self):
        threading.Thread(target=self.receive_acks, daemon=True).start()
        self.send_packets()
        while self.base < TOTAL_PACKETS:
            time.sleep(0.1)
        self.sock.close()
        print("Sender completed transmission.")

if __name__ == '__main__':
    sender = UDPSender()
    sender.run()
