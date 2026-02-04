import os
import uuid
from pathlib import Path

import aiofiles

from app.core.config import settings


class FileStorageService:
    """Local file storage. Can be swapped for S3 later."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)

    async def save_file(
        self,
        file_content: bytes,
        project_id: uuid.UUID,
        filename: str,
    ) -> str:
        """Save file and return relative path."""
        project_dir = self.upload_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid collisions
        file_ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        file_path = project_dir / unique_name

        # Write file synchronously (aiofiles optional for Phase 1)
        with open(file_path, "wb") as f:
            f.write(file_content)

        return str(file_path.relative_to(self.upload_dir))

    async def delete_file(self, relative_path: str) -> None:
        """Delete a stored file."""
        file_path = self.upload_dir / relative_path
        if file_path.exists():
            file_path.unlink()

    async def get_file_path(self, relative_path: str) -> Path:
        """Get absolute path for a stored file."""
        return self.upload_dir / relative_path
