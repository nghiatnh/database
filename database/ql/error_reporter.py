from enum import Enum
from database.ql.token import Token


class ErrorClass(Enum):
  """
  ErrorClass
  ==========
  ErrorClass is an enumeration class that represents the class of an error
  during the compilation process.
  """

  LEXER_ERROR = 1
  PARSER_ERROR = 2
  SEMANTIC_ERROR = 3


class ErrorType(Enum):
  # Lexer errors
  UNCLOSED_COMMENT = 1
  UNCLOSED_QUOTE = 2
  INVALID_CHARACTER = 3
  UNMATCHED_COMMENT = 4

  # Parser errors
  UNEXPECTED_TOKEN = 101
  EXPECT_TOKEN = 102
  INVALID_TYPE = 103

  # Semantic errors
  DUPLICATE_DECLARATION = 201
  UNDECLARED_IDENTIFIER = 202
  INVALID_ASSIGNMENT = 203
  TYPE_MISMATCH = 204
  INVALID_OPERATION = 205
  INVALID_ARGUMENT = 206
  INVALID_RETURN = 207
  INVALID_BREAK = 208
  INVALID_CONTINUE = 209


class CompileError(Exception):
  """
  CompileError
  ============
  CompileError is an exception class that is raised when an error occurs during 
  the  compilation process.
  """

  def __init__(
      self,
      line_text: str,
      error_type: ErrorType,
      line: int,
      column: int,
      message: str = "",
  ) -> None:
    error_class = ErrorClass(error_type.value // 100 + 1)
    error_message = f"\n\n{line_text}\n"
    error_message += " " * (column - 1) + "^\n"
    error_message += (
        f"{error_class.name}: at line {line}, "
        f"column {column}: {message}\n"
    )
    super().__init__(error_message)


class ErrorReporter:
  """
  ErrorReporter
  =============
  ErrorReporter is a class that is responsible for reporting errors during the 
  compilation process.
  """

  def __init__(self, text: str) -> None:
    self.lines = text.split("\n")

  def error_token(
      self, error_type: ErrorType,
      token: Token,
      message: str = "",
  ) -> CompileError:
    """
    Returning a compile error with the given error type and token.
    """
    return CompileError(
        self.lines[token.line - 1], error_type, token.line,
        token.column, message,
    )

  def error(
      self,
      error_type: ErrorType,
      line: int,
      column: int,
      message: str = "",
  ) -> CompileError:
    """
    Returning a compile error with the given error type and token.
    """
    return CompileError(self.lines[line - 1], error_type, line, column, message)
