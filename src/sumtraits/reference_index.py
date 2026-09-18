"""Byte-offset indexes for the taxon-blocked reference data files.

Reference data files hold millions of rows, but all rows for a given taxon are
stored in one contiguous block. An index records the byte offset and length of
each block, so a lookup seeks straight to the few blocks a profile needs
instead of scanning the whole file.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

INDEX_SUFFIX = ".idx"
INDEX_VERSION = 1

_VERSION_KEY = "sumtraits_index_version"
_SIZE_KEY = "reference_size"
_MTIME_KEY = "reference_mtime_ns"

BUILD_COMMAND = "sumtraits-index"

Index = dict[str, tuple[int, int]]


def index_path_for(reference_path: Path) -> Path:
    """Return the sidecar index path for a reference data file."""
    return reference_path.with_name(reference_path.name + INDEX_SUFFIX)


def _iter_blocks(reference_path: Path):
    """Yield (taxon_id, offset, length) for each contiguous taxon block.

    The first line is the header and is not part of any block.
    """
    with open(reference_path, "rb") as reference_file:
        offset = len(reference_file.readline())
        current_taxon_id = None
        block_start = offset

        for line in reference_file:
            taxon_id = line[: line.find(b"\t")]
            if taxon_id != current_taxon_id:
                if current_taxon_id is not None:
                    yield current_taxon_id.decode(), block_start, offset - block_start
                current_taxon_id = taxon_id
                block_start = offset
            offset += len(line)

        if current_taxon_id is not None:
            yield current_taxon_id.decode(), block_start, offset - block_start


def _write_index(index_path: Path, reference_path: Path, blocks) -> int:
    """Write the index via a temporary file so readers never see a partial index."""
    stat = reference_path.stat()
    temporary_path = index_path.with_name(index_path.name + ".tmp")
    seen: set[str] = set()

    with open(temporary_path, "w") as index_file:
        index_file.write(f"#{_VERSION_KEY}={INDEX_VERSION}\n")
        index_file.write(f"#{_SIZE_KEY}={stat.st_size}\n")
        index_file.write(f"#{_MTIME_KEY}={stat.st_mtime_ns}\n")
        index_file.write("taxon_id\toffset\tlength\n")
        for taxon_id, offset, length in blocks:
            # One entry per taxon, so a taxon split across several blocks would
            # silently lose rows. Refuse to build rather than index it wrongly.
            if taxon_id in seen:
                temporary_path.unlink(missing_ok=True)
                raise ValueError(
                    f"{reference_path} is not sorted by taxon_id: rows for taxon "
                    f"{taxon_id} appear in more than one block (second block at "
                    f"byte {offset}). Sort the file by its first column and retry."
                )
            seen.add(taxon_id)
            index_file.write(f"{taxon_id}\t{offset}\t{length}\n")

    os.replace(temporary_path, index_path)
    return len(seen)


def build_index(reference_path: Path) -> Path:
    """Build the sidecar index for a reference data file and return its path."""
    if not reference_path.is_file():
        raise FileNotFoundError(f"Reference data file not found: {reference_path}")

    index_path = index_path_for(reference_path)
    entry_count = _write_index(index_path, reference_path, _iter_blocks(reference_path))
    logger.info("Indexed %d taxa from %s", entry_count, reference_path)
    return index_path


def _parse_header(index_file, index_path: Path) -> dict[str, str]:
    header: dict[str, str] = {}
    for line in index_file:
        if not line.startswith("#"):
            break
        key, _, value = line[1:].strip().partition("=")
        header[key] = value
    else:
        raise ValueError(f"Index file has no column header: {index_path}")
    return header


def _validate_header(
    header: dict[str, str], index_path: Path, reference_path: Path
) -> None:
    version = header.get(_VERSION_KEY)
    if version != str(INDEX_VERSION):
        raise ValueError(
            f"Index {index_path} was built by an incompatible sumtraits version "
            f"(found {version!r}, expected {INDEX_VERSION}). "
            f"Rebuild it with `{BUILD_COMMAND}`."
        )

    # The recorded mtime is provenance only: copying a reference file does not
    # preserve it, so validating against it would fail spuriously.
    indexed_size = header.get(_SIZE_KEY)
    actual_size = reference_path.stat().st_size
    if indexed_size != str(actual_size):
        raise ValueError(
            f"Index {index_path} is stale: it was built for a {indexed_size}-byte "
            f"file but {reference_path} is {actual_size} bytes. "
            f"Rebuild it with `{BUILD_COMMAND}`."
        )


def load_index(reference_path: Path) -> Index:
    """Load the sidecar index, raising if it is missing or stale."""
    index_path = index_path_for(reference_path)
    if not index_path.is_file():
        raise FileNotFoundError(
            f"No index found for {reference_path} (expected {index_path}). "
            f"Build it with `{BUILD_COMMAND} "
            f"--sumtraits-reference-data-dir {reference_path.parent}`."
        )

    with open(index_path, "r") as index_file:
        header = _parse_header(index_file, index_path)
        _validate_header(header, index_path, reference_path)

        index: Index = {}
        for line in index_file:
            taxon_id, offset, length = line.rstrip("\n").split("\t")
            index[taxon_id] = (int(offset), int(length))

    return index


def _read_block(reference_file, taxon_id: str, offset: int, length: int) -> bytes:
    reference_file.seek(offset)
    block = reference_file.read(length)

    expected_prefix = f"{taxon_id}\t".encode()
    if not block.startswith(expected_prefix):
        raise ValueError(
            f"Index points at offset {offset} for taxon {taxon_id}, but the "
            f"reference data does not start with that taxon there. "
            f"Rebuild the index with `{BUILD_COMMAND}`."
        )
    return block


def read_blocks(reference_path: Path, index: Index, tax_ids: set[int]) -> str:
    """Return the header plus every reference row belonging to ``tax_ids``.

    Tax ids missing from the index are skipped, and blocks are read in file
    order, so the result is identical to filtering the file line by line.
    """
    found = [(str(tax_id), index[str(tax_id)]) for tax_id in tax_ids if str(tax_id) in index]
    found.sort(key=lambda entry: entry[1][0])

    with open(reference_path, "rb") as reference_file:
        chunks = [reference_file.readline()]
        chunks.extend(
            _read_block(reference_file, taxon_id, offset, length)
            for taxon_id, (offset, length) in found
        )

    return b"".join(chunks).decode()
