import os
import shutil
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDrag
from PyQt6.QtWidgets import QTreeView, QAbstractItemView, QApplication

class DragDropTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragStartPosition = event.position().toPoint()  # Usar .position() en PyQt6

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.position().toPoint() - self.dragStartPosition).manhattanLength() < QApplication.startDragDistance():
            return
        
        drag = QDrag(self)
        mimedata = self.model().mimeData(self.selectedIndexes())
        drag.setMimeData(mimedata)
        
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.source() == self:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            # Si se arrastran archivos desde fuera
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                target_index = self.indexAt(event.position().toPoint())
                if target_index.isValid():
                    if self.model().isDir(target_index):
                        destination = self.model().filePath(target_index)
                    else:
                        destination = self.model().filePath(target_index.parent())
                else:
                    destination = self.model().rootPath()

                source = url.toLocalFile()
                if os.path.isfile(source):
                    shutil.move(source, os.path.join(destination, os.path.basename(source)))
                elif os.path.isdir(source):
                    shutil.move(source, destination)

            # Actualiza la vista del árbol después de mover los archivos
            self.model().setRootPath(self.model().rootPath())
        elif event.source() == self:
            # Si se arrastran archivos dentro del propio árbol (movimiento interno)
            event.acceptProposedAction()
            target_index = self.indexAt(event.position().toPoint())
            for source_index in self.selectedIndexes():
                source_path = self.model().filePath(source_index)
                if target_index.isValid():
                    if self.model().isDir(target_index):
                        destination_path = self.model().filePath(target_index)
                    else:
                        destination_path = self.model().filePath(target_index.parent())
                else:
                    destination_path = self.model().rootPath()

                # Mover archivos o carpetas internamente
                if os.path.exists(source_path):
                    shutil.move(source_path, os.path.join(destination_path, os.path.basename(source_path)))

            # Actualiza la vista del árbol después de mover los archivos
            self.model().setRootPath(self.model().rootPath())
        else:
            event.ignore()

