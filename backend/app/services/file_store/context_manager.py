import os
from pathlib import Path
from tempfile import NamedTemporaryFile, SpooledTemporaryFile

from types_boto3_s3 import S3Client

from app.core.config import Settings
from app.logger import app_logger
from app.services.file_store.db import S3Service


class S3FileStager:
    """
    Used to create a temporary file and download the target file from Minio to the
    temporary file to be able to have a exposable path for scrappers and
    file processors to work on (ex. Docling).

    This context manager ensures that proper creation and cleanup of temporary file
    is being done. Since the temporary file is being created on the disk and not
    in memory, this removes the need to load file contents to the memory
    which limits the size of file being opened.
    """

    def __init__(
        self,
        s3_service,
        file_key,
        settings,
        temp_file: SpooledTemporaryFile | None = None,
    ):
        self.s3_service: S3Service = s3_service
        self.settings: Settings = settings
        self.file_key: str = file_key
        self.temp_file = None
        self.temp_file_path: Path | None = None
        self.temp_file: SpooledTemporaryFile | None = temp_file

    def _upload_file(self):
        if self.temp_file is None:
            raise ValueError("Temp file argument cannot be empty")
        s3_client: S3Client = self.s3_service.client
        try:
            s3_client.upload_fileobj(
                self.temp_file, self.settings.minio_bucket_name, self.file_key
            )
            return None
        except Exception as e:
            app_logger.error(
                f"Something went wrong during uploading of file to file store: {e}"
            )
            return None

    def __enter__(self) -> Path:
        s3_client: S3Client = self.s3_service.client

        if self.temp_file:
            self._upload_file()

        self.temp_file = NamedTemporaryFile(
            delete=False, suffix=Path(self.file_key).suffix
        )
        self.temp_file_path = Path(self.temp_file.name)
        with self.temp_file as file:
            s3_client.download_fileobj(
                Bucket=self.settings.minio_bucket_name,
                Key=self.file_key,
                Fileobj=file,
            )

        return self.temp_file_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cleanup()

    def _cleanup(self):
        if self.temp_file_path.exists():
            os.remove(self.temp_file_path)
