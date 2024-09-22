class QLError(Exception):
  """
  QLError
  =======
  QLError class represents an error that occurred during the parsing of a query.
  It contains the line and column where the error occurred and the error
  message.
  """

  def __init__(
      self,
      full_text: str,
      line: int,
      column: int,
      message: str,
      *args: object,
  ):
    error_line = full_text.split("\n")[line - 1]
    pointer_line = " " * (column - 1) + "^"
    msg = f"Error:\n{error_line}\n{pointer_line}"
    msg += f"\nError at line {line}, column {column}: {message}"
    super().__init__(msg, *args)
