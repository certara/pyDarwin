
class DarwinError(RuntimeError):
    def __int__(self, error: str):
        super(DarwinError).__init__(error)
