class QLError(Exception):
  def __init__(
          self, line: int, column: int, message: str, *args: object) -> None:
    msg = f"Error at line {line}, column {column}: {message}"
    super().__init__(msg, *args)
