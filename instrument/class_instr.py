import socket
import time
import numpy as np


class instr:


    def __init__(self, name: str, ip_address: str, port=5025, buffer_size=1024, time_out=10, line_ending="\n"):
        self.name = name
        self.ip_address = ip_address
        self.port = port
        self.buffer_size = buffer_size
        self.time_out = time_out
        self.line_ending = line_ending

        self._connection = None
        try:
            # 1. Create and connect the socket
            self._connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._connection.settimeout(self.time_out)
            self._connection.connect((self.ip_address, self.port))

            print(f"Connected to {self.name} [{self.ip_address}:{self.port}].")

        except socket.error as e:
            # Important: Set connection to None on failure
            self._connection = None
            raise ConnectionError(f"Failed to connect to {self.name}: {e}")

    def close(self):
        """Closes the socket connection and cleans up resources."""
        if self._connection:
            self._connection.close()
            self._connection = None

        print(f"Disconnected from {self.name} [{self.ip_address}:{self.port}].")

    def _send_command(self, command: str):
        if not self._connection:
            raise ConnectionError("Connection is not active. Please initialize the driver.")

        full_command = (command + self.line_ending).encode('ascii')

        try:
            self._connection.sendall(full_command)
            # print(f"Sent: {full_command}")

            time.sleep(0.05)  # Give the device a moment to process and respond

            if ("?" in command):
                response = b""
                # Loop to read until a newline character is found (SCPI delimiter)
                while True:
                    chunk = self._connection.recv(self.buffer_size)
                    if not chunk:
                        raise socket.error("Connection closed while reading response.")
                    response += chunk

                    if b"\n" in chunk:
                        break

                return response.decode('ascii').strip()
            else:
                return None

        except socket.timeout:
            raise TimeoutError(f"Command '{command}' timed out.")

        except socket.error as e:
            self._connection = None
            raise IOError(f"Communication error: {e}")




