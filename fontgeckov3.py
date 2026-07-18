#!/usr/bin/env python3
import sys
import os
import shutil
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QListWidget, QLabel, QSplitter, QPushButton, QFileDialog, QLineEdit
from PyQt5.QtGui import QFontDatabase, QFont
from PyQt5.QtCore import Qt

import qdarkstyle #MIT Dark Style
from qdarkstyle import load_stylesheet, DarkPalette

geckoappversion = "v.3.0" 

class FontGecko(QWidget):
    """
    Intaalr una fuente en linux requiere:
    copiar las fuentes a la carpeta ~/.local/share/fonts
    correr fc-cache -f
    rezar...
    Gecko lo resuelve de forma minimalista, recursiva y sin plegarias.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"FontGecko {geckoappversion}")
        self.setGeometry(100, 100, 800, 600)

        # Definir la ruta correcta de fuentes de usuario en Linux
        self.user_fonts_dir = os.path.expanduser("~/.local/share/fonts")
        if not os.path.exists(self.user_fonts_dir):
            os.makedirs(self.user_fonts_dir)

        # Antes de forzar verifica dónde se instaló la fuente con fc-list : file | grep -i [orbitron] o la fuente que sea
        # Forzar a Qt a escanear e inyectar directamente toda tu carpeta local
        # Las fuentes variables son el problema (usar solamente en casos extremos)
        '''
        if os.path.exists(self.user_fonts_dir):
            for archivo in os.listdir(self.user_fonts_dir):
                if archivo.endswith(('.ttf', '.otf')):
                    ruta_completa = os.path.join(self.user_fonts_dir, archivo)
                    QFontDatabase.addApplicationFont(ruta_completa)
        '''
        
        # Forzar la carga manual recorriendo todas las subcarpetas de forma recursiva
        if os.path.exists(self.user_fonts_dir):
            for raiz, subcarpetas, archivos in os.walk(self.user_fonts_dir):
                for archivo in archivos:
                    # Filtramos extensiones y saltamos las problemáticas fuentes variables
                    if archivo.endswith(('.ttf', '.otf')) and "variablefont" not in archivo.lower():
                        ruta_completa = os.path.join(raiz, archivo)
                        QFontDatabase.addApplicationFont(ruta_completa)
        
        # Base de datos de fuentes
        self.db = QFontDatabase()

        self.init_ui()

    def init_ui(self):
        # Layout Principal
        layout = QVBoxLayout()
        
        # Botón para instalar nueva fuente
        self.btn_instalar = QPushButton("Instalar Nueva Fuente (.ttf/.otf)")
        self.btn_instalar.setStyleSheet("background-color: #00ff88; color: #121212; font-weight: bold; padding: 8px;")
        self.btn_instalar.clicked.connect(self.instalar_fuente)
        layout.addWidget(self.btn_instalar)

        # Cuadro de búsqueda brutal
        self.buscador = QLineEdit()
        self.buscador.setPlaceholderText("🔎 Buscar fuente (ej: orbitron)...")
        self.buscador.setStyleSheet("background-color: #2a2a2a; color: #00ff88; border: 1px solid #333; padding: 5px; font-size: 14px;")
        self.buscador.textChanged.connect(self.filtrar_fuentes)
        layout.addWidget(self.buscador)
        
        splitter = QSplitter(Qt.Horizontal)

        # Lista de Fuentes (Izquierda)
        self.lista_fuentes = QListWidget()
        self.actualizar_lista_fuentes()
        self.lista_fuentes.currentTextChanged.connect(self.previsualizar)
        splitter.addWidget(self.lista_fuentes)

        # Previsualización (Derecha)
        self.preview = QLabel("Gecko O\nAaBbCc123\nEl veloz murciélago...")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("border: 1px solid #333; background-color: #1e1e1e; color: #00ff88;")
        self.preview.setFont(QFont("Arial", 24)) 
        splitter.addWidget(self.preview)

        layout.addWidget(splitter)
        self.setLayout(layout)

    def actualizar_lista_fuentes(self):
        """Refresca los elementos de la lista leyendo la base de datos actual de Qt"""
        self.lista_fuentes.clear()
        fuentes = QFontDatabase().families() # Forzamos nueva instancia para leer cambios
        self.lista_fuentes.addItems(fuentes)

    def previsualizar(self, familia):
        """Cambia la fuente del QLabel en tiempo real"""
        if familia:
            fuente = QFont(familia, 24)
            self.preview.setFont(fuente)
            self.preview.setToolTip(f"Familia: {familia}\nEstilos: {', '.join(self.db.styles(familia))}")

    def instalar_fuente(self):
        """Abre un diálogo, copia la fuente al sistema y la inyecta en la app en caliente"""
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Fuente", "", "Fuentes (*.ttf *.otf)")
        
        if archivo:
            nombre_archivo = os.path.basename(archivo)
            destino = os.path.join(self.user_fonts_dir, nombre_archivo)
            
            try:
                # 1. Copiar de forma permanente al sistema
                shutil.copy(archivo, destino)
                
                # 2. Registrar en la sesión actual de la app (Inyección en caliente)
                font_id = QFontDatabase.addApplicationFont(destino)
                
                if font_id != -1:
                    # Obtener el nombre de la familia que acabamos de registrar
                    familias_instaladas = QFontDatabase.applicationFontFamilies(font_id)
                    print(f"¡Fuente cargada con éxito en la app: {familias_instaladas}!")
                    
                    # 3. Correr fc-cache de fondo para que otros programas (GIMP, etc) también la tengan
                    os.system("fc-cache -f")
                    
                    # 4. Actualizar la UI
                    self.actualizar_lista_fuentes()
                    
                    # Seleccionar la nueva fuente instalada automáticamente
                    if familias_instaladas:
                        item = self.lista_fuentes.findItems(familias_instaladas[0], Qt.MatchExactly)
                        if item:
                            self.lista_fuentes.setCurrentItem(item[0])
                else:
                    print("Error: Qt no pudo procesar el archivo de fuente.")
                    
            except Exception as e:
                print(f"Error al copiar el archivo: {e}")

    def filtrar_fuentes(self, texto):
        """Oculta o muestra los ítems de la lista según coincidan con el texto ingresado"""
        texto = texto.lower()
        for i in range(self.lista_fuentes.count()):
            item = self.lista_fuentes.item(i)
            # Si el texto está vacío o coincide parcialmente con el nombre de la fuente, se muestra
            coincide = texto in item.text().lower()
            self.lista_fuentes.setRowHidden(i, not coincide)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(DarkPalette))
    win = FontGecko()
    win.show()
    sys.exit(app.exec_())