from dataclasses import dataclass

from database.utils import binary


@dataclass
class MasterPage:
  # Master page structure:
  # | Signature | Version | Flushed | Root |
  # | 16b       | 8b      | 8b      | 8b   |

  sig: str
  version: int
  flushed: int
  root: int

  def serialize(self) -> bytes:
    return (
        self.sig.encode() +
        binary.bytes8(self.version) +
        binary.bytes8(self.flushed) +
        binary.bytes8(self.root)
    )

  @staticmethod
  def deserialize(data: bytes) -> "MasterPage":
    return MasterPage(
        sig=data[:16].decode(),
        version=binary.int64(data[16:24]),
        flushed=binary.int64(data[24:32]),
        root=binary.int64(data[32:40])
    )
