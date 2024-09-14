from typing import List, Optional
import graphviz

from database.ql.token import Token
from database.ql.constants import ASTNodeType


class ASTNode:
  """
  ASTNode
  =======
  ASTNode class represents a node in the abstract syntax tree. It contains
  a token and a list of children nodes. The token represents the node's value
  and the children represent the node's children.
  """

  def __init__(
      self,
      node_type: ASTNodeType,
      token: Token,
      children: Optional[List["ASTNode"]] = None,
  ):
    self._type = node_type
    self._token = token
    self._children = children or []

  def __str__(self) -> str:
    return f"ASTNode({self.type.name}: {self.token.value})"

  def __repr__(self) -> str:
    return self.__str__()

  @staticmethod
  def _add_node(node: "ASTNode", dot: graphviz.Digraph):
    if node.token and node.token.value is not None:
      dot.node(str(id(node)), f"{node.type.name}: {node.token.value}")
    else:
      dot.node(str(id(node)), f"{node.type.name}")
    for child in node.children:
      ASTNode._add_node(child, dot)
      dot.edge(str(id(node)), str(id(child)))

  # ========================================================================= #
  # Public API                                                                #
  # ========================================================================= #

  @property
  def token(self) -> Token:
    """The token of the node."""
    return self._token

  @property
  def children(self) -> List["ASTNode"]:
    """The children nodes of the node."""
    return self._children

  @property
  def type(self) -> ASTNodeType:
    """The type of the node."""
    return self._type

  def render(self, filename: str):
    """
    Render the abstract syntax tree to a file using graphviz.
    """
    dot = graphviz.Digraph()
    ASTNode._add_node(self, dot)
    dot.render(filename, format="png", view=True)
