import socket
import threading
import time
import os
import sys

stop_threads = False
current_chat_partner = None
my_username = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def recv_thread(sock):
    """Background thread: receive messages from the server."""
    global current_chat_partner
    sock.settimeout(1.0)  # Allow periodic checks for stop_threads

    while not stop_threads:
        try:
            data, _ = sock.recvfrom(4096)
            message = data.decode('utf-8').strip()
        except socket.timeout:
            continue
        except OSError:
            break
        except Exception as e:
            if not stop_threads:
                print(f"\n[ERROR] {e}")
            break

        for line in message.split('\n'):
            line = line.strip()
            if not line or line == "PONG":
                continue

            if line.startswith("LIST:"):
                users = [u for u in line[5:].split(',') if u]
                print("\n--- Online Users ---")
                if users:
                    for u in users:
                        print(f"  - {u}")
                else:
                    print("  (no other users online)")
                print("--------------------")

            elif line.startswith("MSG:"):
                try:
                    _, sender, text = line.split(":", 2)
                    if current_chat_partner == sender:
                        print(f"\r[{sender}] {text}")
                        print("> ", end="", flush=True)
                    else:
                        print(f"\n--- New message from {sender} ---")
                        print(f"  {text}")
                        print("---------------------------------")
                        print("> ", end="", flush=True)
                except ValueError:
                    pass

            elif line.startswith("ERROR:"):
                print(f"\n[!] {line[6:]}")
                print("> ", end="", flush=True)

            elif line.startswith("JOIN:"):
                print(f"\n[+] {line[5:]} joined.")
                print("> ", end="", flush=True)

            elif line.startswith("LEAVE:"):
                print(f"\n[-] {line[6:]} left.")
                print("> ", end="", flush=True)

def ping_thread(sock, server_addr):
    """Send periodic PING to keep the UDP mapping alive (NAT keepalive)."""
    while not stop_threads:
        try:
            sock.sendto(b"PING\n", server_addr)
        except:
            break
        time.sleep(10)

def main():
    global stop_threads, current_chat_partner, my_username

    clear_screen()
    print("=== Python Terminal Chat (UDP) ===")

    # Get server address
    host_port = input("Enter server IP:PORT (default 127.0.0.1:9999): ").strip()
    if not host_port:
        host, port = "127.0.0.1", 9999
    else:
        try:
            host, port_str = host_port.split(":")
            port = int(port_str)
        except ValueError:
            print("Invalid format. Using 127.0.0.1:9999")
            host, port = "127.0.0.1", 9999

    server_addr = (host, port)

    # Get username
    username = input("Enter your username: ").strip()
    while not username:
        username = input("Enter your username: ").strip()
    my_username = username

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', 0))  # Bind to any available local port

    # Log in
    try:
        sock.sendto(f"LOGIN:{username}\n".encode('utf-8'), server_addr)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print(f"\nConnected to {host}:{port} as '{username}'")

    # Start background threads
    t_recv = threading.Thread(target=recv_thread, args=(sock,), daemon=True)
    t_recv.start()

    t_ping = threading.Thread(target=ping_thread, args=(sock, server_addr), daemon=True)
    t_ping.start()

    time.sleep(0.5)  # Let server respond with initial user list

    # Main menu loop
    while True:
        try:
            current_chat_partner = None
            print("\n=== Main Menu ===")
            print("1. List online users")
            print("2. Chat with a user")
            print("3. Quit")
            choice = input("Select: ").strip()

            if choice == "1":
                sock.sendto(b"LIST\n", server_addr)
                time.sleep(0.5)

            elif choice == "2":
                contact = input("Enter username to chat with: ").strip()
                if not contact:
                    continue
                current_chat_partner = contact
                print(f"\n--- Chatting with {contact} ---")
                print("Type your message. Type '/back' to return.")
                while True:
                    try:
                        msg = input("> ").strip()
                        if msg.lower() == "/back":
                            break
                        elif msg:
                            sock.sendto(f"MSG:{contact}:{msg}\n".encode('utf-8'), server_addr)
                    except KeyboardInterrupt:
                        break

            elif choice == "3":
                break
            else:
                print("Invalid choice.")

        except KeyboardInterrupt:
            break

    # Logout
    try:
        sock.sendto(f"LOGOUT:{username}\n".encode('utf-8'), server_addr)
    except:
        pass

    stop_threads = True
    sock.close()
    print("\nDisconnected. Goodbye!")

if __name__ == "__main__":
    main()