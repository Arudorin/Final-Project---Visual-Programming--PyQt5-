import sys
import sqlite3
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QStatusBar, QLabel, QTableWidgetItem, 
    QMessageBox, QFileDialog
)
from PyQt5.uic import loadUi
from PyQt5.QtCore import QDate, Qt

class ExpenseTrackerApp(QMainWindow):
    """
    Kelas aplikasi utama untuk DompetKu - Pelacak Pengeluaran.
    Menangani pemuatan UI, interaksi database, dan event handling.
    """
    def __init__(self):
        super().__init__()
        
        # Memuat file UI yang dibuat dengan Qt Designer
        loadUi("dompetku_main_window.ui", self)
        
        # --- Fitur Wajib: Integrasi Database (SQLite) ---
        self.db_conn = self.init_db()
        
        # --- Fitur Wajib: Status Bar dengan Informasi Mahasiswa ---
        self.setup_statusbar()

        # --- Fitur Wajib: Kustomisasi StyleSheet ---
        self.apply_styles()

        self.current_expense_id = None # Untuk melacak pengeluaran yang dipilih

        # Inisialisasi komponen UI
        self.setup_ui_components()

        # Menghubungkan sinyal dari elemen UI ke slot (metode) yang sesuai
        self.connect_signals()

        # Memuat data awal dari database ke dalam tabel
        self.load_expenses_from_db()

    def init_db(self):
        """
        Menginisialisasi database SQLite dan membuat tabel 'expenses' jika belum ada.
        Tabel memiliki 6 kolom, termasuk ID.
        """
        conn = sqlite3.connect("expenses_database.db")
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                date TEXT,
                amount INTEGER,
                notes TEXT
            )
        """)
        conn.commit()
        return conn

    def setup_statusbar(self):
        """
        --- Fitur Wajib: Status Bar ---
        Mengatur status bar untuk menampilkan informasi mahasiswa yang tidak dapat diedit.
        """
        student_name = "Aldrin Rahmad Aldino" 
        student_id = "F1D022109"
        
        status_label = QLabel(f"  Mahasiswa: {student_name} ({student_id})  ")
        status_label.setObjectName("statusLabel") # Menetapkan nama objek untuk styling
        self.statusbar.addPermanentWidget(status_label)

    def apply_styles(self):
        """
        --- Fitur Wajib: Kustomisasi StyleSheet ---
        Menerapkan gaya kustom mirip CSS untuk tema gelap (dark theme) agar teks terlihat jelas.
        """
        self.setStyleSheet("""
            QWidget {
                background-color: #2E2E2E;
                color: #E0E0E0;
            }
            QMenuBar, QMenu {
                background-color: #404040;
                color: #E0E0E0;
            }
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #444444;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 10px;
                background-color: #404040;
                border-radius: 4px;
            }
            QLineEdit, QTextEdit, QComboBox, QDateEdit, QSpinBox {
                background-color: #3C3C3C;
                color: #E0E0E0;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 4px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                 width: 18px;
            }
            QPushButton {
                background-color: #2a9d8f;
                color: white;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #3bb5a7;
            }
            QPushButton:pressed {
                background-color: #268c80;
            }
            QPushButton#btnHapus {
                background-color: #e76f51;
            }
            QPushButton#btnHapus:hover {
                background-color: #ef8a75;
            }
            QTableWidget {
                background-color: #3C3C3C;
                color: #E0E0E0;
                border: 1px solid #555555;
                gridline-color: #555555;
                font-size: 12px;
                alternate-background-color: #424242;
            }
            QTableWidget::item:selected {
                background-color: #2a9d8f;
                color: white;
            }
            QHeaderView::section {
                background-color: #264653;
                color: white;
                padding: 4px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QLabel#statusLabel {
                font-weight: bold;
                color: #E0E0E0;
            }
        """)

    def setup_ui_components(self):
        """
        Menginisialisasi widget dengan nilai atau konten default.
        """
        self.comboBoxKategori.addItems(["Makanan", "Transportasi", "Hiburan", "Belanja", "Pendidikan", "Kesehatan", "Lainnya"])
        self.dateEditTanggal.setDate(QDate.currentDate())
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setHorizontalHeaderLabels(["ID", "Nama Pengeluaran", "Kategori", "Tanggal", "Jumlah (Rp)", "Keterangan"])
        self.tableWidget.setColumnHidden(0, True) 
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

    def connect_signals(self):
        """
        Menghubungkan sinyal widget ke metode yang sesuai.
        """
        self.actionKeluar.triggered.connect(self.close)
        self.actionTentang.triggered.connect(self.show_about_dialog)
        self.actionEkspor_ke_CSV.triggered.connect(self.export_to_csv)

        self.btnTambah.clicked.connect(self.add_expense)
        self.btnPerbarui.clicked.connect(self.update_expense)
        self.btnHapus.clicked.connect(self.delete_expense)
        self.btnBersihkan.clicked.connect(self.clear_form)

        self.tableWidget.itemClicked.connect(self.populate_form_from_table)
    
    def load_expenses_from_db(self):
        """
        Mengambil semua data pengeluaran dari database dan mengisi QTableWidget.
        """
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, name, category, date, amount, notes FROM expenses")
        
        self.tableWidget.setRowCount(0)
        
        for row_index, row_data in enumerate(cursor.fetchall()):
            self.tableWidget.insertRow(row_index)
            for col_index, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data))
                if col_index == 4: # Kolom Jumlah
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.tableWidget.setItem(row_index, col_index, item)
        
        self.tableWidget.resizeColumnsToContents()
        self.clear_form()

    def add_expense(self):
        """
        Mengumpulkan data dari form dan memasukkan pengeluaran baru ke database.
        """
        name = self.lineEditNama.text().strip()
        if not name:
            QMessageBox.warning(self, "Kesalahan Validasi", "Nama pengeluaran tidak boleh kosong.")
            return

        category = self.comboBoxKategori.currentText()
        date = self.dateEditTanggal.date().toString(Qt.ISODate)
        amount = self.spinBoxJumlah.value()
        notes = self.textEditKeterangan.toPlainText().strip()
        
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT INTO expenses (name, category, date, amount, notes) 
                VALUES (?, ?, ?, ?, ?)
            """, (name, category, date, amount, notes))
            self.db_conn.commit()
            QMessageBox.information(self, "Sukses", "Pengeluaran berhasil ditambahkan!")
            self.load_expenses_from_db()
        except Exception as e:
            QMessageBox.critical(self, "Kesalahan Database", f"Terjadi kesalahan: {e}")

    def update_expense(self):
        """
        Memperbarui pengeluaran yang dipilih dengan data dari form.
        """
        if self.current_expense_id is None:
            QMessageBox.warning(self, "Kesalahan Seleksi", "Silakan pilih data dari tabel untuk diperbarui.")
            return
            
        name = self.lineEditNama.text().strip()
        if not name:
            QMessageBox.warning(self, "Kesalahan Validasi", "Nama pengeluaran tidak boleh kosong.")
            return

        category = self.comboBoxKategori.currentText()
        date = self.dateEditTanggal.date().toString(Qt.ISODate)
        amount = self.spinBoxJumlah.value()
        notes = self.textEditKeterangan.toPlainText().strip()

        try:
            cursor = self.db_conn.cursor()
            cursor.execute("""
                UPDATE expenses 
                SET name=?, category=?, date=?, amount=?, notes=?
                WHERE id=?
            """, (name, category, date, amount, notes, self.current_expense_id))
            self.db_conn.commit()
            QMessageBox.information(self, "Sukses", "Data pengeluaran berhasil diperbarui!")
            self.load_expenses_from_db()
        except Exception as e:
            QMessageBox.critical(self, "Kesalahan Database", f"Terjadi kesalahan: {e}")

    def delete_expense(self):
        """
        Menghapus pengeluaran yang dipilih dari database.
        """
        if self.current_expense_id is None:
            QMessageBox.warning(self, "Kesalahan Seleksi", "Silakan pilih data dari tabel untuk dihapus.")
            return
        
        reply = QMessageBox.question(self, 'Konfirmasi Hapus', 
                                     'Apakah Anda yakin ingin menghapus data ini?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                cursor = self.db_conn.cursor()
                cursor.execute("DELETE FROM expenses WHERE id=?", (self.current_expense_id,))
                self.db_conn.commit()
                QMessageBox.information(self, "Sukses", "Data pengeluaran berhasil dihapus!")
                self.load_expenses_from_db()
            except Exception as e:
                QMessageBox.critical(self, "Kesalahan Database", f"Terjadi kesalahan: {e}")

    def populate_form_from_table(self, item):
        """
        Mengisi form dengan data dari baris tabel yang diklik pengguna.
        """
        current_row = self.tableWidget.currentRow()
        if current_row < 0:
            return

        self.current_expense_id = int(self.tableWidget.item(current_row, 0).text())
        
        self.lineEditNama.setText(self.tableWidget.item(current_row, 1).text())
        self.comboBoxKategori.setCurrentText(self.tableWidget.item(current_row, 2).text())
        date_str = self.tableWidget.item(current_row, 3).text()
        self.dateEditTanggal.setDate(QDate.fromString(date_str, Qt.ISODate))
        self.spinBoxJumlah.setValue(int(self.tableWidget.item(current_row, 4).text()))
        self.textEditKeterangan.setPlainText(self.tableWidget.item(current_row, 5).text())

    def clear_form(self):
        """
        Mengatur ulang semua field form ke keadaan default.
        """
        self.current_expense_id = None
        self.lineEditNama.clear()
        self.comboBoxKategori.setCurrentIndex(0)
        self.dateEditTanggal.setDate(QDate.currentDate())
        self.spinBoxJumlah.setValue(0)
        self.textEditKeterangan.clear()
        self.tableWidget.clearSelection()

    def export_to_csv(self):
        """
        --- Fitur Wajib: Fitur Ekspor ---
        Mengekspor semua data dari tabel 'expenses' ke file CSV.
        """
        try:
            cursor = self.db_conn.cursor()
            cursor.execute("SELECT name, category, date, amount, notes FROM expenses")
            rows = cursor.fetchall()
            
            if not rows:
                QMessageBox.information(self, "Tidak Ada Data", "Tidak ada data untuk diekspor.")
                return

            path, _ = QFileDialog.getSaveFileName(self, "Simpan File CSV", "", "CSV Files (*.csv)")

            if path:
                with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Nama Pengeluaran", "Kategori", "Tanggal", "Jumlah", "Keterangan"])
                    writer.writerows(rows)
                
                QMessageBox.information(self, "Sukses", f"Data berhasil diekspor ke {path}")

        except Exception as e:
            QMessageBox.critical(self, "Kesalahan Ekspor", f"Terjadi kesalahan saat ekspor: {e}")

    def show_about_dialog(self):
        """
        Menampilkan dialog 'Tentang' sederhana dengan detail aplikasi.
        """
        QMessageBox.about(self, "Tentang DompetKu",
                          "<b>DompetKu - Pelacak Pengeluaran</b><br><br>"
                          "Aplikasi ini dibuat untuk Proyek Akhir mata kuliah Pemrograman Visual.<br><br>"
                          "Aldrin Rahmad Aldino (F1D022109)<br>"
                          "<b>Versi:</b> 1.0")

    def closeEvent(self, event):
        """
        Menimpa event close default untuk memastikan koneksi database ditutup.
        """
        self.db_conn.close()
        event.accept()

# --- Titik Masuk Aplikasi ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpenseTrackerApp()
    window.show()
    sys.exit(app.exec_())
