#!/usr/bin/env python3
"""Workspace Setups manager - ventana normal del sistema para gestionar
los espacios de trabajo del plugin karel.workspace-setups (barra Omarchy).

Lee y escribe ~/.config/omarchy/workspace-setups.json, el mismo archivo
que el plugin vigila, asi que los cambios se reflejan al instante.
"""
import json
import os
import subprocess
import sys

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMessageBox, QPushButton, QSpinBox,
    QStackedWidget, QStyle, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

CONFIG_PATH = os.path.expanduser("~/.config/omarchy/workspace-setups.json")

STYLE = """
/* Tema Omarchy (Catppuccin Mocha) */
* { font-family: "JetBrainsMono Nerd Font", "Noto Sans", sans-serif; }
QWidget { background: #1e1e2e; color: #cdd6f4; font-size: 13px; }
QMainWindow, QDialog { background: #1e1e2e; }

QListWidget, QTableWidget, QLineEdit, QSpinBox, QComboBox {
    background: #181825; border: 1px solid #313244; border-radius: 8px;
    padding: 6px; selection-background-color: #45475a;
    selection-color: #cdd6f4; outline: none;
}
QListWidget { padding: 8px; }
QListWidget::item {
    border-radius: 8px; padding: 8px 12px; margin: 2px 0;
}
QListWidget::item:hover { background: #313244; }
QListWidget::item:selected { background: #45475a; border: 1px solid #585b70; }

QLineEdit, QSpinBox, QComboBox { min-height: 20px; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus { border: 1px solid #89b4fa; }

QPushButton {
    background: #313244; border: 1px solid #45475a; border-radius: 8px;
    padding: 9px 16px; color: #cdd6f4;
}
QPushButton:hover { background: #45475a; border-color: #585b70; }
QPushButton:pressed { background: #585b70; }
QPushButton:disabled { color: #6c7086; background: #181825; border-color: #313244; }
QPushButton#primary {
    background: #89b4fa; color: #11111b; font-weight: bold; border: none;
}
QPushButton#primary:hover { background: #b4befe; }
QPushButton#danger { background: #313244; color: #f38ba8; }
QPushButton#danger:hover { background: #f38ba8; color: #11111b; }

QLabel#title { font-size: 19px; font-weight: bold; color: #cdd6f4; }
QLabel#muted { color: #7f849c; font-size: 12px; }
QLabel#section { color: #89b4fa; font-weight: bold; font-size: 12px;
    letter-spacing: 1px; }

QHeaderView::section {
    background: #181825; color: #7f849c; border: none;
    padding: 6px; font-size: 11px; letter-spacing: 1px;
}
QTableWidget { gridline-color: #313244; }
QTableWidget::item { border: none; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid #45475a; background: #181825;
}
QCheckBox::indicator:checked { background: #89b4fa; border-color: #89b4fa; }

QScrollBar:vertical { background: #1e1e2e; width: 10px; margin: 0; }
QScrollBar::handle:vertical {
    background: #45475a; border-radius: 5px; min-height: 24px;
}
QScrollBar::handle:vertical:hover { background: #585b70; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QToolTip { background: #313244; color: #cdd6f4; border: 1px solid #45475a;
    padding: 5px; }
"""


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        setups = data.get("setups") or []
        return [s for s in setups if isinstance(s, dict) and s.get("name")]
    except (OSError, json.JSONDecodeError):
        return []


def save_config(setups):
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"setups": setups}, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, CONFIG_PATH)


def launch_setup(index):
    """Abre el setup via el launcher compartido (reglas por clase fiables)."""
    launcher = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "launch.sh")
    subprocess.Popen(["bash", launcher, str(index)])


class SetupEditor(QDialog):
    """Formulario de un espacio: nombre, icono, escritorio destino y apps."""

    def __init__(self, parent=None, setup=None):
        super().__init__(parent)
        self.setWindowTitle("Espacio de trabajo")
        self.setMinimumWidth(560)
        setup = setup or {}
        editing = bool(setup)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        title = QLabel("󰏫  Editar espacio" if editing else "󰐕  Nuevo espacio")
        title.setObjectName("title")
        layout.addWidget(title)

        general = QLabel("GENERAL")
        general.setObjectName("section")
        layout.addWidget(general)

        form = QFormLayout()
        form.setSpacing(8)

        self.name_edit = QLineEdit(setup.get("name", ""))
        self.name_edit.setPlaceholderText("Ej. Desarrollo")
        form.addRow("Nombre", self.name_edit)

        self.icon_edit = QLineEdit(setup.get("icon", ""))
        self.icon_edit.setPlaceholderText("Glifo Nerd Font, ej. 󰨞 (opcional)")
        form.addRow("Icono", self.icon_edit)

        self.switch_check = QCheckBox("Ir al escritorio al abrir")
        self.switch_spin = QSpinBox()
        self.switch_spin.setRange(1, 9999)
        self.switch_spin.setValue(setup.get("switchTo") or 1)
        self.switch_spin.setEnabled("switchTo" in setup)
        self.switch_check.setChecked("switchTo" in setup)
        self.switch_check.toggled.connect(self.switch_spin.setEnabled)
        row = QHBoxLayout()
        row.addWidget(self.switch_check)
        row.addWidget(self.switch_spin)
        row.addStretch(1)
        form.addRow(row)

        layout.addLayout(form)

        apps_label = QLabel("APLICACIONES")
        apps_label.setObjectName("section")
        layout.addWidget(apps_label)
        apps_hint = QLabel("Cada fila abre el comando en su escritorio.")
        apps_hint.setObjectName("muted")
        layout.addWidget(apps_hint)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ESCRITORIO", "COMANDO", ""])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        for app in setup.get("apps") or []:
            ws_val = app.get("workspace")
            self.add_app_row(1 if ws_val is None else ws_val,
                             app.get("command", ""))
        if self.table.rowCount() == 0:
            self.add_app_row()
        layout.addWidget(self.table)

        add_btn = QPushButton("󰐕  Agregar aplicación")
        add_btn.clicked.connect(lambda: self.add_app_row())
        layout.addWidget(add_btn)

        note = QLabel(
            "Nota: una misma app solo puede ir a un escritorio por sesión "
            "(limitación de Hyprland).")
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        buttons.button(QDialogButtonBox.StandardButton.Save).setObjectName("primary")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        buttons.accepted.connect(self.on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add_app_row(self, workspace=1, command=""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        ws = QSpinBox()
        ws.setRange(1, 9999)
        ws.setValue(workspace)
        self.table.setCellWidget(row, 0, ws)
        cmd = QLineEdit(command)
        cmd.setPlaceholderText("comando, ej. firefox")
        self.table.setCellWidget(row, 1, cmd)
        remove = QPushButton("󰅖")
        remove.setObjectName("danger")
        remove.setFixedSize(QSize(30, 30))
        remove.clicked.connect(lambda: self.remove_app_row(row))
        self.table.setCellWidget(row, 2, remove)

    def remove_app_row(self, row):
        sender_row = self.table.indexAt(self.sender().pos()).row()
        if sender_row >= 0:
            self.table.removeRow(sender_row)

    def on_save(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Falta el nombre",
                                "Escribe un nombre para el espacio.")
            return
        if not self.result_setup()["apps"]:
            QMessageBox.warning(self, "Sin aplicaciones",
                                "Agrega al menos una aplicación con comando.")
            return
        self.accept()

    def result_setup(self):
        apps = []
        for row in range(self.table.rowCount()):
            ws = self.table.cellWidget(row, 0)
            cmd = self.table.cellWidget(row, 1)
            if cmd and cmd.text().strip():
                apps.append({"workspace": ws.value(),
                             "command": cmd.text().strip()})
        setup = {"name": self.name_edit.text().strip(), "apps": apps}
        icon = self.icon_edit.text().strip()
        if icon:
            setup["icon"] = icon
        if self.switch_check.isChecked():
            setup["switchTo"] = self.switch_spin.value()
        return setup


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Espacios de trabajo")
        self.setMinimumSize(560, 420)
        self.setups = load_config()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("󰀻  Espacios de trabajo")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch(1)
        count_lbl = QLabel()
        count_lbl.setObjectName("muted")
        self.count_lbl = count_lbl
        header.addWidget(count_lbl)
        layout.addLayout(header)

        subtitle = QLabel(
            "Doble click para abrir un espacio · selecciona para gestionar")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)

        list_label = QLabel("ESPACIOS")
        list_label.setObjectName("section")
        layout.addWidget(list_label)

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(
            lambda item: self.launch(self.list.row(item)))
        layout.addWidget(self.list)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        self.open_btn = QPushButton("󰁔  Abrir")
        self.open_btn.setObjectName("primary")
        self.new_btn = QPushButton("󰐕  Nuevo")
        self.edit_btn = QPushButton("󰏫  Editar")
        self.dup_btn = QPushButton("󰆏  Duplicar")
        self.del_btn = QPushButton("󰆴  Eliminar")
        self.del_btn.setObjectName("danger")
        self.open_btn.clicked.connect(lambda: self.launch(self.list.currentRow()))
        self.new_btn.clicked.connect(self.new_setup)
        self.edit_btn.clicked.connect(lambda: self.edit(self.list.currentRow()))
        self.dup_btn.clicked.connect(lambda: self.duplicate(self.list.currentRow()))
        self.del_btn.clicked.connect(lambda: self.delete(self.list.currentRow()))
        buttons.addWidget(self.open_btn)
        buttons.addStretch(1)
        for b in (self.new_btn, self.edit_btn, self.dup_btn, self.del_btn):
            buttons.addWidget(b)
        layout.addLayout(buttons)

        self.refresh()

    def refresh(self):
        self.list.clear()
        n = len(self.setups)
        self.count_lbl.setText(f"{n} espacio" + ("" if n == 1 else "s"))
        for setup in self.setups:
            icon = setup.get("icon") or "󰍹"
            apps = "  ·  ".join(
                f"{a.get('workspace', '?')} {(a.get('command') or '').split()[0]}"
                for a in setup.get("apps") or [])
            item = QListWidgetItem(
                f"{icon}  {setup['name']}\n     {apps or 'Sin aplicaciones'}")
            item.setSizeHint(QSize(0, 48))
            self.list.addItem(item)

    def persist(self):
        save_config(self.setups)
        self.refresh()

    def launch(self, index):
        if 0 <= index < len(self.setups):
            launch_setup(index)

    def new_setup(self):
        editor = SetupEditor(self)
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.setups.append(editor.result_setup())
            self.persist()

    def edit(self, index):
        if not (0 <= index < len(self.setups)):
            return
        editor = SetupEditor(self, self.setups[index])
        if editor.exec() == QDialog.DialogCode.Accepted:
            self.setups[index] = editor.result_setup()
            self.persist()

    def duplicate(self, index):
        if not (0 <= index < len(self.setups)):
            return
        import copy
        clone = copy.deepcopy(self.setups[index])
        clone["name"] = clone["name"] + " (copia)"
        self.setups.insert(index + 1, clone)
        self.persist()

    def delete(self, index):
        if not (0 <= index < len(self.setups)):
            return
        name = self.setups[index]["name"]
        answer = QMessageBox.question(
            self, "Eliminar", f'¿Eliminar "{name}"?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes:
            self.setups.pop(index)
            self.persist()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
