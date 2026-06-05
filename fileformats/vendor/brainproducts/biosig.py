"""

Authors:
- Miao Cao
- Thomas G. Close

Email:
- miaocao@swin.edu.au
"""

from fileformats.core import validated_property
from fileformats.core.exceptions import FormatMismatchError
from fileformats.generic import BinaryFile, UnicodeFile
from fileformats.core.mixin import WithAdjacentFiles
from fileformats.biosig import Biosig


class WithBrainVisionMagic:
    """Checks the 'Brain Vision' magic string in text mode, handling optional BOM via utf-8-sig."""

    @validated_property
    def brain_vision_magic(self) -> None:
        first_line = self.fspath.read_text(encoding="utf-8-sig").split("\n")[0]  # type: ignore[attr-defined]
        if not first_line.startswith("Brain Vision"):
            raise FormatMismatchError(
                f"File does not start with 'Brain Vision' magic string: {self}"
            )


class BrainVisionHeader(WithBrainVisionMagic, UnicodeFile, Biosig):
    """
    BrainVision header file (.vhdr) — plain-text INI file describing channel
    configuration, sampling rate, amplifier settings, and references to the
    data and marker files.
    """

    ext = ".vhdr"


class BrainVisionMarker(WithBrainVisionMagic, UnicodeFile, Biosig):
    """
    BrainVision marker file (.vmrk) — plain-text INI file containing event
    markers and annotations time-stamped to samples in the data file.
    """

    ext = ".vmrk"


class BrainVision(WithAdjacentFiles, BinaryFile, Biosig):
    """
    BrainVision binary data file (.eeg) — raw multiplexed sample data,
    format described by the accompanying .vhdr header file. No magic number.
    """

    ext = ".eeg"

    @validated_property
    def header_file(self) -> BrainVisionHeader:
        return BrainVisionHeader(self.select_by_ext(BrainVisionHeader))

    @validated_property
    def marker_file(self) -> BrainVisionMarker:
        return BrainVisionMarker(self.select_by_ext(BrainVisionMarker))
