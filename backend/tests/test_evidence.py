
from pathlib import Path

from app.retrieval.chunker import __file__ as chunker_file
from app.retrieval.retriever import __file__ as retriever_file
from app.retrieval.citations import __file__ as citations_file
from app.services.evidence_service import __file__ as evidence_service_file


def test_evidence_modules_exist():
    """Verify that the Phase 4 modules are available."""
    module_files = [
        chunker_file,
        retriever_file,
        citations_file,
        evidence_service_file,
    ]

    for file_path in module_files:
        assert Path(file_path).is_file()
