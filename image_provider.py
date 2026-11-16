from __future__ import annotations

import hashlib
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest

from paths import cache_dir


class ImageProvider(QObject):
    """Асинхронная загрузка аватаров и иконок героев с дисковым кешем."""

    pixmap_ready = Signal(str, QPixmap)
    failed = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._manager = QNetworkAccessManager(self)
        self._memory: dict[str, QPixmap] = {}
        self._pending: set[str] = set()
        self._failed: set[str] = set()
        self._folder = cache_dir() / "images"
        self._folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _normalize(url: str) -> str:
        url = (url or "").strip()
        if url.startswith("//"):
            return "https:" + url
        return url

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()
        return self._folder / f"{digest}.png"

    def get(self, url: str) -> QPixmap | None:
        url = self._normalize(url)
        if not url:
            return None
        if url in self._memory:
            return self._memory[url]
        if url in self._failed:
            return None

        path = self._cache_path(url)
        if path.exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self._memory[url] = pixmap
                return pixmap

        self.request(url)
        return None

    def request(self, url: str) -> None:
        url = self._normalize(url)
        if (
            not url
            or url in self._memory
            or url in self._pending
            or url in self._failed
        ):
            return

        request = QNetworkRequest(QUrl(url))
        request.setHeader(QNetworkRequest.KnownHeaders.UserAgentHeader, "Dota2Pulse/1.0")
        request.setTransferTimeout(20000)
        self._pending.add(url)
        reply = self._manager.get(request)
        reply.finished.connect(lambda: self._on_finished(url, reply))

    def _on_finished(self, url: str, reply: QNetworkReply) -> None:
        self._pending.discard(url)
        try:
            if reply.error() != QNetworkReply.NetworkError.NoError:
                self._failed.add(url)
                self.failed.emit(url)
                return
            data = reply.readAll()
            pixmap = QPixmap()
            if not pixmap.loadFromData(data):
                self._failed.add(url)
                self.failed.emit(url)
                return
            self._memory[url] = pixmap
            try:
                pixmap.save(str(self._cache_path(url)), "PNG")
            except OSError:
                pass
            self.pixmap_ready.emit(url, pixmap)
        finally:
            reply.deleteLater()
