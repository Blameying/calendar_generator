import socket
import os

# 配置
HOST = "0.0.0.0"  # 监听所有网络接口
PORT = 8122  # 监听的TCP端口
FILE_NAME = (
    "/home/blame/workspace/calendar_generator/compressed_image.bin"  # 要传输的文件名
)


def start_server():
    # 检查文件是否存在
    if not os.path.exists(FILE_NAME):
        print(f"Error: {FILE_NAME} does not exist in the current directory.")
        return

    # 创建 TCP 套接字
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(1)  # 最大等待连接数为 1
    print(f"Server is listening on {HOST}:{PORT}...")

    try:
        while True:
            # 等待客户端连接
            client_socket, client_address = server_socket.accept()
            print(f"Connection established with {client_address}")

            try:
                # 发送文件内容
                with open(FILE_NAME, "rb") as file:
                    while True:
                        data = file.read(1024)  # 每次读取 1024 字节
                        if not data:
                            break
                        client_socket.sendall(data)  # 发送数据
                print(f"File {FILE_NAME} sent successfully to {client_address}")

            except Exception as e:
                print(f"Error while sending file: {e}")

            finally:
                client_socket.close()
                print(f"Connection with {client_address} closed.")

    except KeyboardInterrupt:
        print("\nServer shutting down...")

    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
