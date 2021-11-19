import enum


def is_http_packet(data: str) -> bool:
        return any(data.startswith(verb) for verb in ["GET","HEAD","POST","PUT","DELETE","CONNECT","OPTIONS","TRACE","PATCH","HTTP"])

class Protocol(enum.Enum):
    HTTP = 'HTTP'
    SOCKS = 'SOCKS'
    CONTROL = 'CONTROL'


class Packet():
    def __init__(self,protocol: Protocol, data: bytes):
        self.protocol = protocol
        self.data = data
    
    def __str__(self) -> str:
        return f"Packet type: {self.protocol} and {len(self.data)} bytes"
