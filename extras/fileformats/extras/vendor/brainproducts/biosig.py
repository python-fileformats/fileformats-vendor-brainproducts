import os
import typing as ty
import configparser
from pathlib import Path

import mne.io
import mne.export

from fileformats.core import extra_implementation, FileSet
from fileformats.vendor.brainproducts.biosig import BrainVision
from fileformats.biosig import Biosig

from fileformats.extras.biosig.utils import mne_deidentify


@extra_implementation(FileSet.read_metadata)
def brain_vision_read_metadata(
    bv: BrainVision, **kwargs: ty.Any
) -> ty.Mapping[str, ty.Any]:
    raw = mne.io.read_raw_brainvision(bv.header_file, preload=False, verbose=False)
    return {
        **raw.info.to_json_dict(),
        **_parse_vhdr(bv.header_file),
    }


@extra_implementation(Biosig.deidentify)
def brain_vision_deidentify(
    bv: BrainVision,
    out_dir: os.PathLike[str],
    spec: ty.Any = None,
    **kwargs: ty.Any,
) -> BrainVision:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = mne.io.read_raw_brainvision(bv.header_file, preload=True, verbose=False)
    raw.info = mne_deidentify(raw, spec)
    deid_vhdr = out_dir / "eeg.vhdr"
    mne.export.export_raw(deid_vhdr, raw, fmt="brainvision", overwrite=True)
    return BrainVision(out_dir / "eeg.eeg")


def _parse_vhdr(path: os.PathLike[str]) -> dict[str, ty.Any]:
    """
    Parse a BrainVision .vhdr file (INI format) for fields not exposed by MNE.
    Extracts acquisition settings and the free-text Comment section.
    """
    parser = configparser.RawConfigParser()
    # vhdr files start with a magic line before the first INI section — skip it
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        lines = f.readlines()
    ini_lines = [line for line in lines if not line.startswith("Brain Vision")]
    parser.read_string("".join(ini_lines))

    def get(
        section: ty.Any,
        key: str,
        fallback: ty.Any = None,
    ) -> ty.Any:
        try:
            return parser.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback

    # [Common Infos] uses inconsistent casing across BrainVision versions
    common = next((s for s in parser.sections() if s.lower() == "common infos"), None)

    comment_lines = []
    if parser.has_section("Comment"):
        comment_lines = [v for _, v in parser.items("Comment") if v.strip()]

    return {
        "bv_data_format": get(common, "DataFormat") if common else None,
        "bv_data_orientation": get(common, "DataOrientation") if common else None,
        "bv_n_channels": get(common, "NumberOfChannels") if common else None,
        "bv_sampling_interval_us": get(common, "SamplingInterval") if common else None,
        "bv_binary_format": get("Binary Infos", "BinaryFormat"),
        "bv_comment": "\n".join(comment_lines) if comment_lines else None,
    }
