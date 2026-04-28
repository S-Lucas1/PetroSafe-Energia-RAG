"""
PetroSafe Energia - Cliente MinIO (Data Lake)
Gerencia operações no Data Lake com arquitetura Medallion.
"""

import io
import json
import hashlib
from datetime import datetime
from typing import Optional

from minio import Minio
from minio.error import S3Error
import structlog

from src.utils.config import get_settings

logger = structlog.get_logger()


class DataLakeClient:
    """Cliente para operações no Data Lake MinIO com suporte Medallion."""

    CAMADAS = ("bronze", "silver", "gold")

    def __init__(self):
        settings = get_settings()
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=settings.minio_secure,
        )
        self._garantir_buckets()

    def _garantir_buckets(self):
        """Cria buckets Medallion se não existirem."""
        for camada in self.CAMADAS:
            if not self.client.bucket_exists(camada):
                self.client.make_bucket(camada)
                logger.info("bucket_criado", camada=camada)

    def upload(
        self,
        camada: str,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict] = None,
    ) -> dict:
        """Upload de dados para uma camada do Data Lake."""
        assert camada in self.CAMADAS, f"Camada inválida: {camada}"

        # Calcular checksum
        checksum = hashlib.md5(data).hexdigest()

        # Metadados padrão
        meta = {
            "x-amz-meta-upload-timestamp": datetime.utcnow().isoformat(),
            "x-amz-meta-checksum-md5": checksum,
            "x-amz-meta-camada": camada,
        }
        if metadata:
            import unicodedata
            def _clean(s):
                s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
                return "".join(ch if ch.isprintable() and ord(ch) < 128 else "_" for ch in s)
            meta.update({f"x-amz-meta-{k}": _clean(v) for k, v in metadata.items()})

        result = self.client.put_object(
            bucket_name=camada,
            object_name=path,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
            metadata=meta,
        )

        logger.info(
            "upload_concluido",
            camada=camada,
            path=path,
            tamanho=len(data),
            version_id=result.version_id,
        )

        return {
            "camada": camada,
            "path": path,
            "version_id": result.version_id,
            "checksum_md5": checksum,
            "tamanho_bytes": len(data),
        }

    def download(self, camada: str, path: str) -> bytes:
        """Download de dados de uma camada."""
        response = self.client.get_object(camada, path)
        data = response.read()
        response.close()
        response.release_conn()
        return data

    def listar(self, camada: str, prefixo: str = "") -> list[dict]:
        """Lista objetos em uma camada."""
        objetos = self.client.list_objects(camada, prefix=prefixo, recursive=True)
        return [
            {
                "nome": obj.object_name,
                "tamanho": obj.size,
                "modificado": obj.last_modified.isoformat() if obj.last_modified else None,
                "version_id": obj.version_id,
            }
            for obj in objetos
        ]

    def upload_json(self, camada: str, path: str, data: dict, metadata: Optional[dict] = None) -> dict:
        """Upload de dados JSON."""
        json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        return self.upload(camada, path, json_bytes, "application/json", metadata)

    def download_json(self, camada: str, path: str) -> dict:
        """Download e parse de JSON."""
        data = self.download(camada, path)
        return json.loads(data.decode("utf-8"))
