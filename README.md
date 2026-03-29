# Multi-Client Terminal Chat System (UDP)

A robust, real-time terminal-based chat application built with **Python**. This project demonstrates core networking concepts, concurrent programming, and reliable message handling over the **UDP protocol**.

## 🚀 Features
- **Multi-threaded Architecture:** Handles simultaneous message sending and receiving without blocking.
- **UDP Socket Programming:** Efficient, low-latency communication between clients and a central server.
- **NAT Keepalive (Ping System):** Implements a periodic PING thread to maintain active UDP port mapping via `playit.gg`.
- **User Management:** Supports User Login, Logout, and a dynamic "Online Users" list.
- **Private Messaging:** Direct messaging capabilities via a simple protocol (`MSG:target:text`).

## 🛠️ Technical Stack
- **Language:** Python 3.x
- **Libraries:** `socket`, `threading`, `time`, `os`
- **Hosting:** Port forwarding handled via `ply.gg` for public access.

## ⚙️ How to Run
1. Run the client on your terminal:
   ```bash
   python client.py
