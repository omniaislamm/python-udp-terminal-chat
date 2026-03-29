import socket
import threading

HOST = '0.0.0.0'
PORT = 9999

# Maps username -> (ip, port)
clients = {}
# Maps (ip, port) -> username
addr_to_user = {}
lock = threading.Lock()

def broadcast(message, exclude_addr=None):
    """Send a message to all connected clients except one."""
    with lock:
        for user, addr in clients.items():
            if addr != exclude_addr:
                try:
                    server.sendto(message.encode('utf-8'), addr)
                except Exception as e:
                    print(f"[ERROR] Broadcast to {user}: {e}")

def send_to(addr, message):
    """Send a message to a specific address."""
    try:
        server.sendto(message.encode('utf-8'), addr)
    except Exception as e:
        print(f"[ERROR] send_to {addr}: {e}")

def handle_message(data, addr):
    """Process a single incoming UDP datagram."""
    try:
        msg = data.decode('utf-8').strip()
    except:
        return

    if msg.startswith("LOGIN:"):
        username = msg.split(":", 1)[1].strip()
        with lock:
            # Check for duplicate username
            if username in clients:
                send_to(addr, "ERROR:Username already taken.\n")
                return
            # Remove old registration for this address if any
            old_user = addr_to_user.get(addr)
            if old_user and old_user in clients:
                del clients[old_user]

            clients[username] = addr
            addr_to_user[addr] = username
            print(f"[REGISTERED] {username} from {addr}")

            # Send online user list to the new user
            others = [u for u in clients if u != username]
            send_to(addr, f"LIST:{','.join(others)}\n")

        # Notify others
        broadcast(f"JOIN:{username}\n", exclude_addr=addr)

    elif msg == "LIST":
        with lock:
            user = addr_to_user.get(addr)
            if not user:
                send_to(addr, "ERROR:Not logged in.\n")
                return
            others = [u for u in clients if u != user]
            send_to(addr, f"LIST:{','.join(others)}\n")

    elif msg.startswith("MSG:"):
        # Format: MSG:recipient:text
        try:
            _, recipient, text = msg.split(":", 2)
        except ValueError:
            send_to(addr, "ERROR:Invalid format. Use MSG:recipient:text\n")
            return

        with lock:
            sender = addr_to_user.get(addr)
            if not sender:
                send_to(addr, "ERROR:Not logged in.\n")
                return
            target_addr = clients.get(recipient)

        if target_addr:
            send_to(target_addr, f"MSG:{sender}:{text}\n")
        else:
            send_to(addr, f"ERROR:User '{recipient}' is not online.\n")

    elif msg == "PING":
        # Heartbeat to keep connection alive / verify still online
        with lock:
            user = addr_to_user.get(addr)
        if user:
            send_to(addr, "PONG\n")

    elif msg.startswith("LOGOUT:"):
        with lock:
            user = addr_to_user.pop(addr, None)
            if user and user in clients:
                del clients[user]
                print(f"[LOGOUT] {user} from {addr}")
        if user:
            broadcast(f"LEAVE:{user}\n")

def main():
    global server
    print("[STARTING] UDP Server is starting...")
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    print(f"[LISTENING] Server is listening on {HOST}:{PORT} (UDP)")

    try:
        while True:
            try:
                data, addr = server.recvfrom(4096)
                # Handle each message in a thread to avoid blocking
                t = threading.Thread(target=handle_message, args=(data, addr))
                t.daemon = True
                t.start()
            except Exception as e:
                print(f"[ERROR] {e}")
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server shutting down...")
    finally:
        server.close()

if __name__ == "__main__":
    main()
