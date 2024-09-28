from enum import Enum


# =========================================================================== #
# Enumerations                                                                #
# =========================================================================== #

class TokenType(Enum):
  EMPTY = ""
  # Single-character tokens
  LEFT_PAREN = "("
  RIGHT_PAREN = ")"
  COMMA = ","
  SEMICOLON = ";"
  SINGLE_QUOTE = "'"
  NEWLINE = "\n"

  # Binary operators
  PLUS = "+"
  MINUS = "-"
  STAR = "*"
  SLASH = "/"
  PERCENT = "%"

  # Comparison operators
  EQ = "="
  NEQ = "!="
  LT = "<"
  LE = "<="
  GT = ">"
  GE = ">="

  # Logical operators
  AND = "AND"
  OR = "OR"
  NOT = "NOT"

  # Keywords
  CREATE = "CREATE"
  DROP = "DROP"
  TABLE = "TABLE"
  INTEGER = "INTEGER"
  TEXT = "TEXT"
  PRIMARY = "PRIMARY"
  KEY = "KEY"
  SELECT = "SELECT"
  AS = "AS"
  FROM = "FROM"
  INDEX = "INDEX"
  BY = "BY"
  FILTER = "FILTER"
  OFFSET = "OFFSET"
  LIMIT = "LIMIT"
  INSERT = "INSERT"
  INTO = "INTO"
  VALUES = "VALUES"
  UPDATE = "UPDATE"
  SET = "SET"
  DELETE = "DELETE"

  # OTHERS
  ID = "ID"
  VALUE = "VALUE"

  EOF = "EOF"


class ASTNodeType(Enum):
  EMPTY = "EMPTY"

  STATEMENTS = "STATEMENTS"
  STATEMENT = "STATEMENT"
  CREATE_TABLE = "CREATE_TABLE"
  DROP_TABLE = "DROP_TABLE"
  DECLARATIONS = "DECLARATIONS"
  FIELD_DECLS = "FIELD_DECLS"
  FIELD_DECL = "FIELD_DECL"
  INDEX_DECLS = "INDEX_DECLS"
  INDEX_DECL = "INDEX_DECL"
  PRIMARY_KEY_DECLS = "PRIMARY_KEY_DECLS"
  PRIMARY_KEY_DECL = "PRIMARY_KEY_DECL"
  SELECT = "SELECT"
  SELECT_EXPR = "SELECT_EXPR"
  AS_EXPR = "AS_EXPR"
  CONDITIONS = "CONDITIONS"
  CONDITION = "CONDITION"
  OFFSET = "OFFSET"
  LIMIT = "LIMIT"
  INDEX = "INDEX"
  FILTER = "FILTER"
  INSERT = "INSERT"
  UPDATE = "UPDATE"
  DELETE = "DELETE"
  TUPLE_DECLS = "TUPLE_DECLS"
  TUPLE_VALUES = "TUPLE_VALUES"
  SET_EXPRS = "SET_EXPRS"
  SET_EXPR = "SET_EXPR"
  NUMBER = "NUMBER"
  STRING = "STRING"
  LOGIC = "LOGIC"
  COMPARISON = "COMPARISON"
  ARITHMETIC = "ARITHMETIC"
  UNARY = "UNARY"
  ID = "ID"
  TYPE = "TYPE"


class IndexOp(Enum):
  EQ = "="
  NEQ = "!="
  LT = "<"
  LE = "<="
  GT = ">"
  GE = ">="


# =========================================================================== #
# Constants                                                                   #
# =========================================================================== #

PUNCTUATIONS = {
    TokenType.LEFT_PAREN.value: TokenType.LEFT_PAREN,
    TokenType.RIGHT_PAREN.value: TokenType.RIGHT_PAREN,
    TokenType.COMMA.value: TokenType.COMMA,
    TokenType.SEMICOLON.value: TokenType.SEMICOLON,
    TokenType.SINGLE_QUOTE.value: TokenType.SINGLE_QUOTE,
}

OPERATORS1CHAR = {
    TokenType.PLUS.value: TokenType.PLUS,
    TokenType.MINUS.value: TokenType.MINUS,
    TokenType.STAR.value: TokenType.STAR,
    TokenType.SLASH.value: TokenType.SLASH,
    TokenType.PERCENT.value: TokenType.PERCENT,
    TokenType.EQ.value: TokenType.EQ,
    TokenType.LT.value: TokenType.LT,
    TokenType.GT.value: TokenType.GT,
}

OPERATORS2CHAR = {
    TokenType.NEQ.value: TokenType.NEQ,
    TokenType.LE.value: TokenType.LE,
    TokenType.GE.value: TokenType.GE,
}

KEYWORDS = {
    TokenType.AND.value: TokenType.AND,
    TokenType.OR.value: TokenType.OR,
    TokenType.NOT.value: TokenType.NOT,
    TokenType.SELECT.value: TokenType.SELECT,
    TokenType.AS.value: TokenType.AS,
    TokenType.FROM.value: TokenType.FROM,
    TokenType.INDEX.value: TokenType.INDEX,
    TokenType.BY.value: TokenType.BY,
    TokenType.FILTER.value: TokenType.FILTER,
    TokenType.CREATE.value: TokenType.CREATE,
    TokenType.DROP.value: TokenType.DROP,
    TokenType.TABLE.value: TokenType.TABLE,
    TokenType.DELETE.value: TokenType.DELETE,
    TokenType.INSERT.value: TokenType.INSERT,
    TokenType.INTO.value: TokenType.INTO,
    TokenType.VALUES.value: TokenType.VALUES,
    TokenType.UPDATE.value: TokenType.UPDATE,
    TokenType.SET.value: TokenType.SET,
    TokenType.LIMIT.value: TokenType.LIMIT,
    TokenType.OFFSET.value: TokenType.OFFSET,
    TokenType.INTEGER.value: TokenType.INTEGER,
    TokenType.TEXT.value: TokenType.TEXT,
    TokenType.PRIMARY.value: TokenType.PRIMARY,
    TokenType.KEY.value: TokenType.KEY,
}
