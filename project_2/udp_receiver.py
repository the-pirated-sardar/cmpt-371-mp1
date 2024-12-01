import socket
import random

# Constants
LOCAL_ADDRESS = ('localhost', 10000)
PACKET_CORRUPTION_PROBABILITY = 0.1  # Probability to simulate packet corruption

class UDPReceiver:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(LOCAL_ADDRESS)
        self.expected_seq_num = 0
        self.buffer = {}

    def run(self):
        print('Receiver is running...')
        while True:
            try:
                data, address = self.sock.recvfrom(1024)
                
                # Simulate packet corruption
                if random.random() < PACKET_CORRUPTION_PROBABILITY:
                    print("Simulated corruption: Packet received is corrupted")
                    continue  # Discard the packet
                
                # Decode and parse the packet
                try:
                    packet = data.decode()
                    seq_num_str, message = packet.split(':', 1)
                    seq_num = int(seq_num_str)
                except (ValueError, IndexError):
                    print("Malformed packet received. Ignoring.")
                    continue
                
                print(f"Received Packet: {seq_num} with message: {message}")

                if seq_num == self.expected_seq_num:
                    print(f"Packet {seq_num} is in order.")
                    self.expected_seq_num += 1
                    # Deliver any buffered packets
                    while self.expected_seq_num in self.buffer:
                        print(f"Delivering buffered Packet {self.expected_seq_num}")
                        del self.buffer[self.expected_seq_num]
                        self.expected_seq_num += 1
                elif seq_num > self.expected_seq_num:
                    print(f"Packet {seq_num} is out of order. Buffering it.")
                    self.buffer[seq_num] = message
                else:
                    print(f"Packet {seq_num} is a duplicate. Ignoring.")

                # Send ACK for the last in-order packet
                ack_packet = str(self.expected_seq_num - 1).encode()
                self.sock.sendto(ack_packet, address)
                print(f"Sent ACK: {self.expected_seq_num - 1}")
            except KeyboardInterrupt:
                print("Receiver shutting down.")
                break
            except Exception as e:
                print(f"Error occurred: {e}")

if __name__ == '__main__':
    receiver = UDPReceiver()
    receiver.run()
