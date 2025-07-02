import sys
import os
import platform
import pyodbc
import logging
from collections import deque
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
                             QTabWidget, QTextEdit, QMessageBox, QGroupBox, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAction, QMenu, QDialog,
                             QDialogButtonBox, QInputDialog, QFormLayout, QAbstractItemView,
                             QSplitter)
from PyQt5.QtCore import (Qt)
from PyQt5 import QtGui
import math
import argparse

parser = argparse.ArgumentParser(
    description='SQL Column Adder - v1.0',
    epilog='Desarrollado por Ivan Gulfo (ivansicol@gmail.com)'
)

class SQLServerColumnAdder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SQL Server Column Adder")
        self.setGeometry(100, 100, 900, 700)
        
        # Configuración de logging
        logging.basicConfig(filename='sql_column_adder.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')
        
        self.connection = None
        self.setup_ui()
        
    def setup_ui(self):
        # Widget central y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Pestañas
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Pestaña de conexión
        self.setup_connection_tab(tab_widget)
        
        # Pestaña de configuración de columnas
        self.setup_column_tab(tab_widget)
        
        # Pestaña de registro
        self.setup_log_tab(tab_widget)

        self.setup_about_dialog()
        
        # Barra de estado
        self.statusBar().showMessage("Listo")
        
        #Cargar log al inicio
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging para escribir en archivo y en la UI"""
        log_file = 'sql_column_adder.log'
        
        # Crear logger
        self.logger = logging.getLogger('SQLColumnAdder')
        self.logger.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Handler para archivo
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Handler para la UI
        class QTextEditLogger(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget
            
            def emit(self, record):
                msg = self.format(record)
                self.widget.append(msg)
                # Auto-scroll
                self.widget.moveCursor(QtGui.QTextCursor.End)
        
        ui_handler = QTextEditLogger(self.log_output)
        ui_handler.setFormatter(formatter)
        
        # Agregar handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(ui_handler)
        
        # Cargar log existente
        self.load_initial_log()
        
    def load_initial_log(self):
        """Carga el historial del log al iniciar"""
        log_file = 'sql_column_adder.log'
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    # Leer las últimas 500 líneas para no sobrecargar la UI
                    lines = deque(f, maxlen=500)
                    self.log_output.setPlainText(''.join(lines)+'============================== LOG ANTIGUO CARGADO =============================')
                    self.log_output.moveCursor(QtGui.QTextCursor.End)
        except Exception as e:
            self.logger.error(f"Error al cargar log inicial: {str(e)}")
    
    def log(self, message, level=logging.INFO):
        """Registra un mensaje en el log y en la interfaz"""
        logging.log(level, message)
        self.log_output.append(f"[{level}] {message}")
        
        # Mostrar mensajes importantes en la barra de estado
        if level >= logging.WARNING:
            self.statusBar().showMessage(message, 5000)
    
    def setup_about_dialog(self):
        about_action = QAction('Acerca de', self)
        about_action.triggered.connect(self.show_about)
        self.menuBar().addAction(about_action)

    def show_about(self):
        QMessageBox.about(self, "Acerca de SQL Column Adder",
                        """<b>SQL Column Adder v1.0</b><br><br>
                        Aplicación para agregar columnas a tablas de SQL Server<br><br>
                        Desarrollado por: <b>Ivan Gulfo</b><br>
                        Empresa: Ivan Gulfo Enterprises<br>
                        Contacto: ivansicol@gmail.com<br>
                        © 2025 Todos los derechos reservados""")
        
    def setup_connection_tab(self, tab_widget):
        connection_tab = QWidget()
        layout = QVBoxLayout(connection_tab)
        
        # Grupo de conexión
        connection_group = QGroupBox("Configuración de Conexión")
        connection_layout = QVBoxLayout()
        
        # Servidor
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Servidor:"))
        self.server_input = QLineEdit("localhost")
        server_layout.addWidget(self.server_input)
        
        # Base de datos
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Base de Datos:"))
        self.db_input = QLineEdit()
        db_layout.addWidget(self.db_input)
        
        # Autenticación
        auth_layout = QHBoxLayout()
        auth_layout.addWidget(QLabel("Autenticación:"))
        self.auth_combo = QComboBox()
        combo_drivers = pyodbc.drivers()
        if platform.system() == "Windows":
            combo_drivers.append("Windows")
        self.auth_combo.addItems(combo_drivers)
        self.auth_combo.currentTextChanged.connect(self.toggle_auth_fields)
        auth_layout.addWidget(self.auth_combo)
        
        # Usuario y contraseña (solo para SQL Server auth)
        self.user_layout = QHBoxLayout()
        self.user_layout.addWidget(QLabel("Usuario:"))
        self.user_input = QLineEdit("sa")
        self.user_layout.addWidget(self.user_input)
        
        self.pass_layout = QHBoxLayout()
        self.pass_layout.addWidget(QLabel("Contraseña:"))
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_layout.addWidget(self.pass_input)
        
        # Botones de conexión
        button_layout = QHBoxLayout()
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.connect_to_db)
        button_layout.addWidget(self.connect_button)
        
        self.disconnect_button = QPushButton("Desconectar")
        self.disconnect_button.clicked.connect(self.disconnect_from_db)
        self.disconnect_button.setEnabled(False)
        button_layout.addWidget(self.disconnect_button)
        
        # Agregar al layout de conexión
        connection_layout.addLayout(server_layout)
        connection_layout.addLayout(db_layout)
        connection_layout.addLayout(auth_layout)
        connection_layout.addLayout(self.user_layout)
        connection_layout.addLayout(self.pass_layout)
        connection_layout.addLayout(button_layout)
        connection_group.setLayout(connection_layout)
        
        # Grupo de esquema/tabla
        table_group = QGroupBox("Selección de Tabla")
        table_layout = QVBoxLayout()
        
        # Esquema
        schema_layout = QHBoxLayout()
        schema_layout.addWidget(QLabel("Esquema:"))
        self.schema_combo = QComboBox()
        schema_layout.addWidget(self.schema_combo)
        
        # Tabla
        table_select_layout = QHBoxLayout()
        table_select_layout.addWidget(QLabel("Tabla:"))
        self.table_combo = QComboBox()
        table_select_layout.addWidget(self.table_combo)
        
        # Botón para refrescar tablas
        refresh_button = QPushButton("Refrescar Tablas")
        refresh_button.clicked.connect(self.refresh_tables)
        table_select_layout.addWidget(refresh_button)
        
        table_layout.addLayout(schema_layout)
        table_layout.addLayout(table_select_layout)
        table_group.setLayout(table_layout)
        
        # Agregar grupos a la pestaña
        layout.addWidget(connection_group)
        layout.addWidget(table_group)
        layout.addStretch()
        
        tab_widget.addTab(connection_tab, "Conexión")
        
        # Inicialmente ocultar campos de usuario/contraseña
        self.toggle_auth_fields()
    
    def setup_column_tab(self, tab_widget):
        column_tab = QWidget()
        layout = QVBoxLayout(column_tab)

        # Grupo para columnas existentes con acciones
        self.existing_columns_group = QGroupBox("Columnas Existentes")
        columns_layout = QVBoxLayout()
        
        # Título dinámico
        self.table_title_label = QLabel("Tabla: Ninguna seleccionada")
        self.table_title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        columns_layout.addWidget(self.table_title_label)
        
        # Tabla de columnas existentes con menú contextual
        self.existing_columns_table = QTableWidget()
        self.existing_columns_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.existing_columns_table.resizeColumnsToContents() 
        self.existing_columns_table.setColumnCount(5)  # +1 columna para acciones
        self.existing_columns_table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Nulo", "Valor Pred.", "Posición"])
        self.existing_columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.existing_columns_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.existing_columns_table.customContextMenuRequested.connect(self.show_column_context_menu)
        
        columns_layout.addWidget(self.existing_columns_table)
        self.existing_columns_group.setLayout(columns_layout)
        
        # Grupo para múltiples columnas (reemplaza el simple)
        multi_column_group = QGroupBox("Gestión Avanzada de Columnas")
        multi_layout = QVBoxLayout()
        
        # Tabla para edición múltiple
        self.multi_columns_table = QTableWidget()
        self.multi_columns_table.resizeColumnsToContents() 
        self.multi_columns_table.setColumnCount(6)
        self.multi_columns_table.setHorizontalHeaderLabels(["Nombre", "Tipo", "Parámetros", "Nullable", "Default", "Posición"])
        self.multi_columns_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Barra de herramientas
        tool_layout = QHBoxLayout()
        
        add_row_btn = QPushButton("➕ Agregar Columna")
        add_row_btn.clicked.connect(self.add_multi_column_row)
        
        remove_row_btn = QPushButton("➖ Eliminar Selección")
        remove_row_btn.clicked.connect(self.remove_multi_column_row)
        
        clear_btn = QPushButton("🧹 Limpiar Todo")
        clear_btn.clicked.connect(self.clear_multi_columns)
        
        execute_btn = QPushButton("💾 Guardar Cambios")
        execute_btn.clicked.connect(self.save_multi_columns)
        execute_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        
        tool_layout.addWidget(add_row_btn)
        tool_layout.addWidget(remove_row_btn)
        tool_layout.addWidget(clear_btn)
        tool_layout.addStretch()
        tool_layout.addWidget(execute_btn)
        
        multi_layout.addWidget(self.multi_columns_table)
        multi_layout.addLayout(tool_layout)
        multi_column_group.setLayout(multi_layout)
        
        #Tabla arriba
        layout.addWidget(self.existing_columns_group)
        
        # Crear un splitter horizontal que contendrá las dos tablas
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.existing_columns_table)
        splitter.addWidget(self.multi_columns_table)

        # Configurar el splitter para que inicialmente divida el espacio por igual
        splitter.setSizes([int(self.width()/2), int(self.width()/2)])

        #Spliter
        layout.addWidget(splitter)

        #Tabla abajo
        layout.addWidget(multi_column_group)
        
        tab_widget.addTab(column_tab, "Gestión de Columnas")
    
    def show_column_context_menu(self, position):
        menu = QMenu()
        selected_row = self.existing_columns_table.currentRow()
        
        if selected_row >= 0:
            rename_action = menu.addAction("✏️ Renombrar Columna")
            edit_action = menu.addAction("⚙️ Modificar Tipo/Default")
            delete_action = menu.addAction("🗑️ Eliminar Columna")
            
            action = menu.exec_(self.existing_columns_table.viewport().mapToGlobal(position))
            
            col_name = self.existing_columns_table.item(selected_row, 0).text()
            
            if action == rename_action:
                self.rename_column(selected_row)
            elif action == edit_action:
                self.edit_column(selected_row)
            elif action == delete_action:
                self.delete_column(selected_row)
    
    def edit_column(self):
        selected = self.existing_columns_table.currentRow()
        if selected >= 0:
            column_name = self.existing_columns_table.item(selected, 0).text()
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Editar columna: {column_name}")
            layout = QVBoxLayout()
            
            # Tipo de dato
            type_label = QLabel("Tipo de dato:")
            type_combo = QComboBox()
            type_combo.addItems(["int", "varchar", "datetime", "decimal", "bit"])
            
            # Longitud/Precisión
            params_label = QLabel("Parámetros:")
            params_input = QLineEdit()
            
            # Valor por defecto
            default_label = QLabel("Valor por defecto:")
            default_input = QLineEdit()
            
            # Botones
            button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            
            layout.addWidget(type_label)
            layout.addWidget(type_combo)
            layout.addWidget(params_label)
            layout.addWidget(params_input)
            layout.addWidget(default_label)
            layout.addWidget(default_input)
            layout.addWidget(button_box)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                self.statusBar().showMessage(f"Actualizando columna {column_name}...")
                try:
                    # Implementar lógica de actualización
                    new_type = type_combo.currentText()
                    params = params_input.text()
                    default = default_input.text()
                    
                    # Ejecutar ALTER TABLE en SQL Server
                    self.execute_column_change(column_name, new_type, params, default)
                    self.statusBar().showMessage(f"Columna {column_name} actualizada con éxito...")
                    
                    self.load_table_columns()  # Refrescar
                    
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))

    def add_multi_column_row(self, column_data=None):
        """Añade una nueva fila con datos opcionales (para edición)"""
        row = self.multi_columns_table.rowCount()
        self.multi_columns_table.insertRow(row)
        
        # Configurar widgets para cada celda
        name_item = QTableWidgetItem(column_data['name'] if column_data else "")
        self.multi_columns_table.setItem(row, 0, name_item)
        
        type_combo = QComboBox()
        types = ["int", "bigint", "smallint", "tinyint", "bit",
            "decimal", "numeric", "money", "smallmoney",
            "float", "real",
            "date", "datetime", "datetime2", "smalldatetime", "time",
            "char", "varchar", "text", "nchar", "nvarchar", "ntext",
            "binary", "varbinary", "image",
            "uniqueidentifier", "xml", "sql_variant"]
        type_combo.addItems(types)
        if column_data:
            base_type = column_data['type'].split('(')[0]
            type_combo.setCurrentText(base_type)
        self.multi_columns_table.setCellWidget(row, 1, type_combo)
        
        params = ""
        if column_data and '(' in column_data['type']:
            params = column_data['type'].split('(')[1].split(')')[0]

        params_item = QTableWidgetItem(params)
        self.multi_columns_table.setItem(row, 2, params_item)
        
        allow_null = QCheckBox(column_data['allow_null'] if column_data else "")
        self.multi_columns_table.setCellWidget(row, 3, allow_null)

        default_item = QTableWidgetItem(column_data['default'] if column_data else "")
        self.multi_columns_table.setItem(row, 4, default_item)
        
        position_combo = QComboBox()
        position_combo.addItem("(al inicio)", "-1")
        for i in range(self.existing_columns_table.rowCount()):
            col_name = self.existing_columns_table.item(i, 0).text()
            position_combo.addItem(col_name, col_name)
        if column_data and column_data['after']:
            idx = position_combo.findData(column_data['after'])
            if idx >= 0:
                position_combo.setCurrentIndex(idx+1)

        position_combo.addItem("(al final)", None)
        self.multi_columns_table.setCellWidget(row, 5, position_combo)

    def clear_multi_columns(self):
        """Limpia toda la tabla de edición"""
        if self.multi_columns_table.rowCount() > 0:
            reply = QMessageBox.question(
                self,
                "Limpiar tabla",
                "¿Está seguro que desea eliminar todas las columnas de la lista?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.multi_columns_table.setRowCount(0)

    def save_multi_columns(self):
        """Guarda todos los cambios de columnas"""
        if self.multi_columns_table.rowCount() == 0:
            QMessageBox.warning(self, "Tabla vacía", "No hay columnas para guardar")
            return
        
        schema = self.schema_combo.currentText()
        table = self.table_combo.currentText()
        
        if not schema or not table or table == 'Seleccione':
            QMessageBox.warning(self, "Error", "Seleccione esquema y tabla")
            return
        
        # Preparar datos
        columns = []
        for row in range(self.multi_columns_table.rowCount()):
            col_data = {
                'name': self.multi_columns_table.item(row, 0).text(),
                'type': self.multi_columns_table.cellWidget(row, 1).currentText(),
                'params': self.multi_columns_table.item(row, 2).text(),
                'allow_null': self.multi_columns_table.cellWidget(row, 3).isChecked(),
                'default': self.multi_columns_table.item(row, 4).text(),
                'after': self.multi_columns_table.cellWidget(row, 5).currentData(),
            }
            
            # Validación básica
            if not col_data['name']:
                QMessageBox.warning(self, "Error", f"Fila {row+1}: Nombre no puede estar vacío")
                return
                
            columns.append(col_data)
        
        # Confirmación final
        reply = QMessageBox.question(
            self,
            "Confirmar cambios",
            f"¿Aplicar los siguientes cambios a la tabla {schema}.{table}?\n\n" +
            "\n".join([f"- {col['name']} ({col['type']})" for col in columns]),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.apply_column_changes(columns)
                self.load_table_columns()
                QMessageBox.information(self, "Éxito", "Cambios aplicados correctamente")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudieron aplicar los cambios:\n{str(e)}")
            finally:
                self.multi_columns_table.setRowCount(0)  # Limpiar tabla

    def remove_multi_column_row(self):
        """Elimina la fila seleccionada o la última si no hay selección"""
        selected_rows = sorted(set(index.row() for index in self.multi_columns_table.selectedIndexes()))
        
        if not selected_rows:
            # Si no hay selección, preguntar si eliminar la última fila
            last_row = self.multi_columns_table.rowCount() - 1
            if last_row >= 0:
                reply = QMessageBox.question(
                    self,
                    "Eliminar última fila",
                    "¿Eliminar la última fila de la lista?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.multi_columns_table.removeRow(last_row)
            else:
                QMessageBox.warning(
                    self,
                    "Tabla vacía",
                    "No hay filas para eliminar",
                    QMessageBox.Ok
                )
        else:
            # Eliminar filas seleccionadas (en orden inverso para evitar problemas de índices)
            reply = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Eliminar las {len(selected_rows)} filas seleccionadas?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for row in sorted(selected_rows, reverse=True):
                    self.multi_columns_table.removeRow(row)

    def rename_column(self, row):
        old_name = self.existing_columns_table.item(row, 0).text()
        new_name, ok = QInputDialog.getText(
            self,
            "Renombrar Columna",
            f"Nuevo nombre para la columna '{old_name}':",
            QLineEdit.Normal,
            old_name
        )
        
        if ok and new_name and new_name != old_name:
            self.statusBar().showMessage(f"Renombrando columna {old_name}...")
            try:
                schema = self.schema_combo.currentText()
                table = self.table_combo.currentText()
                
                cursor = self.connection.cursor()
                cursor.execute("BEGIN TRANSACTION")

                cursor.execute(f"""
                    EXEC sp_rename '{schema}.{table}.{old_name}', '{new_name}', 'COLUMN'
                """)
                cursor.execute("COMMIT TRANSACTION")
                self.connection.commit()
                
                self.load_table_columns()
                self.log(f"Columna renombrada: {old_name} → {new_name}")
                self.statusBar().showMessage(f"Columna renombrada {old_name} → {new_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo renombrar: {str(e)}")

    def edit_column(self, row):
        # Implementación similar a la anterior pero más completa
        col_name = self.existing_columns_table.item(row, 0).text()
        col_type = self.existing_columns_table.item(row, 1).text()
        col_nullable = self.existing_columns_table.item(row, 2).text() == "Sí"
        col_default = self.existing_columns_table.item(row, 3).text()
        
        dialog = ColumnEditorDialog(col_name, col_type, col_nullable, col_default, self)
        if dialog.exec_() == QDialog.Accepted:
            new_def = dialog.get_column_data()
            try:
                # Implementar lógica ALTER COLUMN según el RDBMS
                self.execute_column_change(col_name, new_def)
                self.load_table_columns()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def execute_column_change(self, old_name, new_data):
        """
        Ejecuta los cambios en una columna existente
        :param old_name: Nombre actual de la columna
        :param new_data: Diccionario con:
            - 'type': Nuevo tipo de dato (ej. "varchar(255)")
            - 'nullable': Si permite NULL
            - 'default': Valor por defecto
        """
        schema = self.schema_combo.currentText()
        table = self.table_combo.currentText()
        
        if not schema or not table or table == 'Seleccione':
            raise ValueError("Esquema y tabla deben estar seleccionados")

        self.statusBar().showMessage(f"Actualizando columna {old_name}...")
        try:
            cursor = self.connection.cursor()
            cursor.execute("BEGIN TRANSACTION")

            # 2. Alterar tipo de dato y nulabilidad
            alter_sql = f"ALTER TABLE [{schema}].[{table}] ALTER COLUMN [{old_name}] {new_data['type']}"
            alter_sql += " NULL" if new_data.get('nullable', True) else " NOT NULL"
            
            cursor.execute(alter_sql)
            
            # 3. Manejar valor por defecto
            if 'default' in new_data:
                # Primero eliminar el default existente si hay uno
                cursor.execute(f"""
                    DECLARE @constraint_name NVARCHAR(256)
                    SELECT @constraint_name = name 
                    FROM sys.default_constraints
                    WHERE parent_object_id = OBJECT_ID('{schema}.{table}')
                    AND parent_column_id = (
                        SELECT column_id 
                        FROM sys.columns 
                        WHERE object_id = OBJECT_ID('{schema}.{table}') 
                        AND name = '{old_name}'
                    )
                    
                    IF @constraint_name IS NOT NULL
                        EXEC('ALTER TABLE [{schema}].[{table}] DROP CONSTRAINT ' + @constraint_name)
                """)
                
                # Agregar nuevo default si se especificó
                if new_data['default']:
                    default_value = new_data['default']
                    # Manejar valores especiales como funciones
                    if default_value.upper() in ('GETDATE()', 'NEWID()'):
                        default_expr = default_value
                    else:
                        # Determinar si necesita comillas
                        if any(t in new_data['type'].lower() for t in ['char', 'text', 'date', 'time']):
                            default_expr = f"N'{default_value}'" if 'n' in new_data['type'].lower() else f"'{default_value}'"
                        else:
                            default_expr = default_value
                    
                    cursor.execute(f"""
                        ALTER TABLE [{schema}].[{table}] 
                        ADD CONSTRAINT [DF_{table}_{old_name}] 
                        DEFAULT {default_expr} FOR [{old_name}]
                    """)
            
            cursor.execute("COMMIT TRANSACTION")
            self.connection.commit()
            self.log(f"Columna {old_name} modificada exitosamente")
            self.statusBar().showMessage(f"Columna {old_name} modificada exitosamente")

        except Exception as e:
            cursor.execute("ROLLBACK TRANSACTION")
            self.log(f"Error al modificar columna {old_name}: {str(e)}", level=logging.ERROR)
            raise
                
    def delete_column(self, row):
        col_name = self.existing_columns_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar permanentemente la columna '{col_name}'?\nEsta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage(f"Eliminando columna {col_name}...")
            try:
                schema = self.schema_combo.currentText()
                table = self.table_combo.currentText()
                
                cursor = self.connection.cursor()
                cursor.execute("BEGIN TRANSACTION")

                cursor.execute(f"""
                    DECLARE @constraint_name NVARCHAR(256)
                    SELECT @constraint_name = name 
                    FROM sys.default_constraints
                    WHERE parent_object_id = OBJECT_ID('{schema}.{table}')
                    AND parent_column_id = (
                        SELECT column_id 
                        FROM sys.columns 
                        WHERE object_id = OBJECT_ID('{schema}.{table}') 
                        AND name = '{col_name}'
                    )
                    
                    IF @constraint_name IS NOT NULL
                        EXEC('ALTER TABLE [{schema}].[{table}] DROP CONSTRAINT ' + @constraint_name)
                """)

                cursor.execute(f"ALTER TABLE [{schema}].[{table}] DROP COLUMN [{col_name}]")
                cursor.execute("COMMIT TRANSACTION")
                self.connection.commit()
                
                self.load_table_columns()
                self.log(f"Columna eliminada: {col_name}")
                self.statusBar().showMessage(f"Columna eliminada: {col_name}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar: {str(e)}")

    def setup_log_tab(self, tab_widget):
        log_tab = QWidget()
        layout = QVBoxLayout(log_tab)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        
        layout.addWidget(self.log_output)
        tab_widget.addTab(log_tab, "Registro")
    
    def toggle_auth_fields(self):
        auth_type = self.auth_combo.currentText()
        if auth_type == "Windows":
            self.user_input.setVisible(False)
            self.user_layout.itemAt(0).widget().setVisible(False)
            self.pass_input.setVisible(False)
            self.pass_layout.itemAt(0).widget().setVisible(False)
        else:
            self.user_input.setVisible(True)
            self.user_layout.itemAt(0).widget().setVisible(True)
            self.pass_input.setVisible(True)
            self.pass_layout.itemAt(0).widget().setVisible(True)
    
    def get_driver_specific_params(self, driver_name):
        driver_name_lower = driver_name.lower()
        
        # Detección por patrones en el nombre del driver
        if 'freetds' in driver_name_lower:
            return {"TDS_Version": "8.0"}
        elif 'odbc driver 13' in driver_name_lower:
            return {"Encrypt": "yes", "TrustServerCertificate": "no"}
        elif 'odbc driver' in driver_name_lower:
            return {"Encrypt": "optional", "TrustServerCertificate": "no"}
        elif 'native client' in driver_name_lower:
            return { "TrustServerCertificate": "yes"}
        elif 'msodbcsql17' in driver_name_lower:
            return {"Encrypt": "optional"}
        elif 'sql server' in driver_name_lower and not ('odbc driver' in driver_name_lower):
            return {}  # Driver genérico (pocos parámetros extra)
        else:
            # Parámetros por defecto para drivers desconocidos (puedes ajustarlos)
            return {"Encrypt": "optional"}
   
    def connect_to_db(self):
        server = self.server_input.text()
        database = self.db_input.text()
        auth_type = self.auth_combo.currentText()
        
        if not server or not database:
            QMessageBox.warning(self, "Error", "Servidor y base de datos son requeridos")
            return
        
        try:
            if auth_type == "Windows":
                conn_str = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;"
            else:
                username = self.user_input.text()
                password = self.pass_input.text()
                
                # Construye la cadena base
                conn_str = f"DRIVER={{{auth_type}}};SERVER={server};DATABASE={database};UID={username};PWD={password};"
                
                # Añade parámetros específicos detectados automáticamente
                driver_params = self.get_driver_specific_params(auth_type)
                for key, value in driver_params.items():
                    conn_str += f"{key}={value};"
            
            self.statusBar().showMessage("Conectando a la base de datos...")
            self.connection = pyodbc.connect(conn_str)

            # Resto del código...
            self.statusBar().showMessage(f"Conectado a {server}/{database}")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            
            # Cargar esquemas
            self.load_schemas()
            
            self.log("Conexión exitosa a la base de datos")
            # Simular operación larga
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error de Conexión", str(e))
            self.log(f"Error de conexión: {str(e)}", level=logging.ERROR)

    def disconnect_from_db(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.statusBar().showMessage("Desconectado")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.schema_combo.clear()
            self.table_combo.clear()
            self.existing_columns_table.setRowCount(0)
            self.log("Desconectado de la base de datos")
    
    def load_schemas(self):
        if not self.connection:
            return
        
        self.statusBar().showMessage("Cargando schemas...")
        try:
            # Crear nuevo cursor
            cursor = self.connection.cursor()


            cursor.execute("""
                SELECT name 
                FROM sys.schemas 
                WHERE name NOT IN ('guest', 'INFORMATION_SCHEMA', 'sys', 'db_owner', 'db_accessadmin', 
                                 'db_securityadmin', 'db_ddladmin', 'db_backupoperator', 
                                 'db_datareader', 'db_datawriter', 'db_denydatareader', 'db_denydatawriter')
                ORDER BY name
            """)
            
            self.schema_combo.clear()
            for row in cursor:
                self.schema_combo.addItem(row.name)
            
            self.log("Esquemas cargados exitosamente")
            self.statusBar().showMessage("Esquemas cargados exitosamente")

            self.refresh_tables()
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los esquemas: {str(e)}")
            self.log(f"Error al cargar esquemas: {str(e)}", level=logging.ERROR)
    
    def refresh_tables(self):
        schema = self.schema_combo.currentText()
        if not schema or not self.connection:
            return
        
        self.statusBar().showMessage(f"Cargando tablas del esquema {schema}...")
        try: 
            
            # Crear nuevo cursor
            cursor = self.connection.cursor()

            cursor.execute(f"""
                SELECT t.name 
                FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = ?
                ORDER BY t.name
            """, schema)
            
            self.table_combo.clear()
            self.table_combo.addItem("Seleccione")
            for row in cursor:
                self.table_combo.addItem(row.name)

            # Cuando se selecciona una tabla, cargar sus columnas
            self.table_combo.currentTextChanged.connect(self.load_table_columns)
            
            #self.load_table_columns()
            self.log(f"Tablas del esquema {schema} cargadas exitosamente")
            self.statusBar().showMessage(f"Tablas del esquema {schema} cargadas exitosamente")
            
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las tablas: {str(e)}")
            self.log(f"Error al cargar tablas: {str(e)}", level=logging.ERROR)
    
    def load_table_columns(self):
        schema = self.schema_combo.currentText()
        table = self.table_combo.currentText()
        
        if not schema or not table or not self.connection:
            return
        
        if table == 'Seleccione':
            return
        
        self.statusBar().showMessage(f"Cargando columnas de la tabla {table}...")
        self.table_title_label.setText(f"Tabla: [{schema}].[{table}]")
        try:

            # Crear nuevo cursor
            cursor = self.connection.cursor()
            
            # Obtener información de columnas con orden explícito por column_id
            cursor.execute(f"""
                SELECT 
                    c.name AS column_name,
                    tp.name AS type_name,
                    c.max_length,
                    c.precision,
                    c.scale,
                    c.is_nullable,
                    ISNULL(dc.definition, '') AS default_value,
                    c.column_id
                FROM sys.columns c
                JOIN sys.types tp ON c.user_type_id = tp.user_type_id
                JOIN sys.tables t ON c.object_id = t.object_id
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
                WHERE s.name = ? AND t.name = ?
                ORDER BY c.column_id
            """, schema, table)
            
            columns = cursor.fetchall()

            # Limpiar y configurar la tabla
            self.existing_columns_table.setRowCount(len(columns))

            columns_list = list(columns)  # Convertir a lista explícita
            for i, col in enumerate(columns_list):
                # Nombre
                self.existing_columns_table.setItem(i, 0, QTableWidgetItem(col.column_name))
                
                # Tipo con parámetros
                type_str = col.type_name
                if col.type_name in ('varchar', 'char'):
                    type_str += f"({col.max_length})"
                elif col.type_name in ('nvarchar', 'nchar'):
                    type_str += f"({math.floor(col.max_length/2)})"
                elif col.type_name in ('decimal', 'numeric'):
                    type_str += f"({col.precision},{col.scale})"
                elif col.type_name in ('datetime2', 'datetimeoffset', 'time'):
                    type_str += f"({col.scale})"
                
                self.existing_columns_table.setItem(i, 1, QTableWidgetItem(type_str))
                
                # Nulo
                nullable_item = QTableWidgetItem()
                nullable_item.setData(Qt.DisplayRole, "Sí" if col.is_nullable else "No")
                self.existing_columns_table.setItem(i, 2, nullable_item)
                
                # Valor por defecto
                self.existing_columns_table.setItem(i, 3, QTableWidgetItem(col.default_value))
                
                # Posición
                self.existing_columns_table.setItem(i, 4, QTableWidgetItem(str(col.column_id)))

            self.log(f"Columnas de {schema}.{table} cargadas exitosamente")
            self.statusBar().showMessage(f"Columnas de {schema}.{table} cargadas exitosamente")
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las columnas de la tabla {table}: {str(e)}")
            self.log(f"Error al cargar columnas de la tabla {table}: {str(e)}", level=logging.ERROR)
    
    def getNewCreateTable(self, create_table, columns): 
        for column in columns:
            # Parsear el SQL para encontrar la lista de columnas
            opening_paren_index = create_table.index('(')
            closing_paren_index = create_table.rindex(')')
            
            before_columns = create_table[:opening_paren_index + 1]
            columns_part = create_table[opening_paren_index + 1:closing_paren_index]
            after_columns = create_table[closing_paren_index:]
            
            # Dividir las columnas existentes, manteniendo las comas originales
            existing_columns = [line.strip() for line in columns_part.split('\n') 
                                if line.strip() and not line.strip().startswith('CONSTRAINT')]
            
            # Construir definición de la nueva columna
            column_def = f"[{column['name']}] {column['type']}({column['params']})" if column['params'] else  f"[{column['name']}] {column['type']}"
            
            if not column['allow_null']:
                column_def += " NOT NULL"
            
            if column['default']:
                if column['default'].upper() in ('GETDATE()', 'SYSDATETIME()', 'NEWID()', 'NEWSEQUENTIALID()', 'CURRENT_TIMESTAMP'):
                    column_def += f" DEFAULT {column['default']}"
                elif  column['type'] in ('int', 'bigint', 'smallint', 'tinyint', 'bit', 'decimal', 'numeric', 
                                    'float', 'real', 'money', 'smallmoney'):
                    column_def += f" DEFAULT {column['default']}"
                else:
                    column_def += f" DEFAULT N'{column['default']}'"
            
            column_def += ","
            
            # Encontrar posición para insertar
            if column['after']:
                # Buscar la columna después de la cual insertar
                if(column['after'] == "-1"):
                    existing_columns.insert(0, column_def)

                for i, col in enumerate(existing_columns):
                    if f"[{column['after']}]" in col:
                        existing_columns.insert(i + 1, column_def)
                        break
                else:
                    # Si no se encuentra, agregar al final
                    if(column['after'] != "-1"):
                        existing_columns.append(column_def)
            else:
                # Agregar al final
                existing_columns.append(column_def)
            
            # Encontrar constraints para mantenerlas al final
            constraints = [line.strip() for line in columns_part.split('\n') 
                            if line.strip().startswith('CONSTRAINT')]
            
            # Reconstruir el SQL
            all_columns = existing_columns + constraints
            new_columns_part = '\n'.join(all_columns)
            create_table = before_columns + new_columns_part + after_columns

        #self.log(create_table)
        return create_table

    def apply_column_changes(self, columns):
        """Aplica todos los cambios de columnas en una sola transacción"""
        schema = self.schema_combo.currentText()
        table = self.table_combo.currentText()

        # Validaciones
        if not schema or not table or table == 'Seleccione':
            QMessageBox.warning(self, "Error", "Seleccione un esquema y una tabla")
            return

        try:
            self.statusBar().showMessage("Agregando nuevas columnas...")
            cursor = self.connection.cursor()
            
            # Ejecutar en una transacción
            self.log(f"Iniciando transacción para agregar columna(s)")
            cursor.execute("BEGIN TRANSACTION")
            
            try:
                # 1. Crear tabla temporal con los datos
                self.log("Creando tabla temporal...")
                cursor.execute(f"""
                    SELECT * INTO [{schema}].[{table}_TEMP] 
                    FROM [{schema}].[{table}]
                """)
                
                # 2. Obtener y eliminar FK que referencian esta tabla
                self.log("Manejando claves foráneas...")
                cursor.execute(f"""
                    SELECT 
                        fk.name AS constraint_name,
                        sch.name AS schema_name,
                        tab.name AS table_name,
                        'ALTER TABLE [' + sch.name + '].[' + tab.name + '] ADD CONSTRAINT [' + fk.name + '] ' +
                        'FOREIGN KEY (' + 
                        STUFF((
                            SELECT ', [' + col.name + ']'
                            FROM sys.foreign_key_columns fkc
                            JOIN sys.columns col ON fkc.parent_object_id = col.object_id AND fkc.parent_column_id = col.column_id
                            WHERE fkc.constraint_object_id = fk.object_id
                            FOR XML PATH('')
                        ), 1, 2, '') + 
                        ') REFERENCES [{schema}].[{table}] (' +
                        STUFF((
                            SELECT ', [' + col.name + ']'
                            FROM sys.foreign_key_columns fkc
                            JOIN sys.columns col ON fkc.referenced_object_id = col.object_id AND fkc.referenced_column_id = col.column_id
                            WHERE fkc.constraint_object_id = fk.object_id
                            FOR XML PATH('')
                        ), 1, 2, '') + 
                        ')' AS create_script,
                        'ALTER TABLE [' + sch.name + '].[' + tab.name + '] DROP CONSTRAINT [' + fk.name + ']' AS drop_script
                    FROM sys.foreign_keys fk
                    JOIN sys.tables tab ON fk.parent_object_id = tab.object_id
                    JOIN sys.schemas sch ON tab.schema_id = sch.schema_id
                    WHERE EXISTS (
                        SELECT 1 
                        FROM sys.foreign_key_columns fkc
                        JOIN sys.tables ref_tab ON fkc.referenced_object_id = ref_tab.object_id
                        JOIN sys.schemas ref_sch ON ref_tab.schema_id = ref_sch.schema_id
                        WHERE fkc.constraint_object_id = fk.object_id
                        AND ref_tab.name = '{table}' 
                        AND ref_sch.name = '{schema}'
                    )
                """)
                
                referencing_fks = cursor.fetchall()
                
                for fk in referencing_fks:
                    self.log(f"Eliminando FK {fk.constraint_name} que referencia a {schema}.{table}")
                    cursor.execute(fk.drop_script)

                # self.log("Obtener COLLATION de DATABASE")
                # cursor.execute(f"""
                #     SELECT DATABASEPROPERTYEX(DB_NAME(), 'Collation')
                # """)
                # dbCollation = cursor.fetchone()[0]
                
                # 3. Obtener permisos
                self.log("Obteniendo permisos...")
                cursor.execute(f"""
                    SELECT 
                        perm.permission_name,
                        perm.state_desc,
                        prin.name AS principal_name,
                        prin.type_desc AS principal_type,
                        CONCAT(
                            'REVOKE ', perm.permission_name COLLATE DATABASE_DEFAULT, 
                            ' ON [{schema}].[{table}] FROM [', 
                            prin.name COLLATE DATABASE_DEFAULT, ']'
                        ) AS revoke_script,
                        CASE 
                            WHEN perm.state_desc = 'GRANT_WITH_GRANT_OPTION' 
                            THEN CONCAT(
                                'GRANT ', perm.permission_name COLLATE DATABASE_DEFAULT, 
                                ' ON [{schema}].[{table}] TO [', 
                                prin.name COLLATE DATABASE_DEFAULT, '] WITH GRANT OPTION'
                            )
                            ELSE CONCAT(
                                perm.state_desc COLLATE DATABASE_DEFAULT, ' ', 
                                perm.permission_name COLLATE DATABASE_DEFAULT, 
                                ' ON [{schema}].[{table}] TO [', 
                                prin.name COLLATE DATABASE_DEFAULT, ']'
                            )
                        END AS grant_script
                    FROM sys.database_permissions perm
                    JOIN sys.database_principals prin ON perm.grantee_principal_id = prin.principal_id
                    WHERE perm.major_id = OBJECT_ID('{schema}.{table}')
                """)
                
                table_permissions = cursor.fetchall()
                
                # 4. Obtener DDL completo de la tabla
                self.log("Obteniendo DDL de la tabla...")
                try:
                    # 1. Obtener CREATE TABLE
                    cursor.execute(f"""
                        SELECT 
                            'CREATE TABLE [{schema}].[{table}] (' + CHAR(13) + CHAR(10) +
                            (
                                SELECT 
                                    '    [' + c.name + '] ' + 
                                    tp.name + 
                                    CASE 
                                        WHEN tp.name IN ('varchar', 'char') 
                                        THEN '(' + IIF(c.max_length = -1, 'MAX', CAST(c.max_length AS VARCHAR)) + ')'
                                        WHEN tp.name IN ('nvarchar', 'nchar') 
                                        THEN '(' + IIF(c.max_length = -1, 'MAX', CAST(c.max_length/2 AS VARCHAR)) + ')'
                                        WHEN tp.name IN ('decimal', 'numeric') 
                                        THEN '(' + CAST(c.precision AS VARCHAR) + ',' + CAST(c.scale AS VARCHAR) + ')'
                                        WHEN tp.name IN ('datetime2', 'datetimeoffset', 'time') 
                                        THEN '(' + CAST(c.scale AS VARCHAR) + ')'
                                        ELSE ''
                                    END + 
                                    CASE WHEN c.is_identity = 1 
                                        THEN ' IDENTITY(' + CAST(IDENT_SEED('{schema}.{table}') AS VARCHAR) + 
                                            ',' + CAST(IDENT_INCR('{schema}.{table}') AS VARCHAR) + ')' 
                                        ELSE '' 
                                    END +
                                    CASE WHEN c.is_nullable = 0 THEN ' NOT NULL' ELSE ' NULL' END +
                                    CASE WHEN dc.definition IS NOT NULL 
                                        THEN ' DEFAULT ' + 
                                            CASE 
                                                WHEN dc.definition LIKE '%getdate%' THEN 'GETDATE()'
                                                WHEN dc.definition LIKE '%sysdatetime%' THEN 'SYSDATETIME()'
                                                WHEN dc.definition LIKE '%newid%' THEN 'NEWID()'
                                                WHEN dc.definition LIKE '%newsequentialid%' THEN 'NEWSEQUENTIALID()'
                                                WHEN dc.definition LIKE '%current_timestamp%' THEN 'CURRENT_TIMESTAMP'
                                                ELSE REPLACE(REPLACE(CAST(dc.definition AS NVARCHAR(MAX)), '(', ''), ')', '')
                                            END
                                        ELSE '' 
                                    END +
                                    ',' + CHAR(13) + CHAR(10)
                                FROM sys.columns c
                                JOIN sys.types tp ON c.user_type_id = tp.user_type_id
                                LEFT JOIN sys.default_constraints dc ON c.default_object_id = dc.object_id
                                WHERE c.object_id = OBJECT_ID('{schema}.{table}')
                                ORDER BY c.column_id
                                FOR XML PATH(''), TYPE
                            ).value('.', 'NVARCHAR(MAX)') +
                            
                            CASE 
                                WHEN EXISTS (SELECT 1 FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('{schema}.{table}') AND type = 'PK')
                                THEN 
                                    '    CONSTRAINT [' + (SELECT name FROM sys.key_constraints WHERE parent_object_id = OBJECT_ID('{schema}.{table}') AND type = 'PK') + '] ' +
                                    'PRIMARY KEY ' + 
                                    (SELECT CASE WHEN index_id = 1 THEN 'CLUSTERED' ELSE 'NONCLUSTERED' END 
                                    FROM sys.indexes 
                                    WHERE object_id = OBJECT_ID('{schema}.{table}') AND is_primary_key = 1) +
                                    ' (' + 
                                    (
                                        SELECT STRING_AGG('[' + c.name + ']', ', ')
                                        FROM sys.index_columns ic
                                        JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                                        WHERE ic.object_id = OBJECT_ID('{schema}.{table}') 
                                        AND ic.index_id = (SELECT index_id FROM sys.indexes WHERE object_id = OBJECT_ID('{schema}.{table}') AND is_primary_key = 1)
                                    ) + ')' + CHAR(13) + CHAR(10)
                                ELSE ''
                            END + ')' AS createTable
                    """)
                    create_table = cursor.fetchone()[0] + ";\n"

                    # 2. Obtener índices
                    cursor.execute(f"""
                        SELECT 
                            'CREATE ' + 
                            CASE WHEN i.is_unique = 1 THEN 'UNIQUE ' ELSE '' END +
                            CASE WHEN i.type_desc = 'CLUSTERED' THEN 'CLUSTERED ' ELSE 'NONCLUSTERED ' END +
                            'INDEX [' + i.name + '] ON [{schema}].[{table}] (' +
                            (
                                SELECT STRING_AGG('[' + c.name + ']' + CASE WHEN ic.is_descending_key = 1 THEN ' DESC' ELSE ' ASC' END, ', ')
                                FROM sys.index_columns ic
                                JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
                                WHERE ic.object_id = i.object_id AND ic.index_id = i.index_id AND ic.key_ordinal > 0
                            ) + ')' +
                            CASE 
                                WHEN i.has_filter = 1 
                                THEN ' WHERE ' + REPLACE(REPLACE(CAST(i.filter_definition AS NVARCHAR(MAX)), '[', ''), ']', '')
                                ELSE ''
                            END AS createIdx
                        FROM sys.indexes i
                        WHERE i.object_id = OBJECT_ID('{schema}.{table}') 
                        AND i.is_primary_key = 0 
                        AND i.type_desc IN ('CLUSTERED', 'NONCLUSTERED')
                    """)
                    create_idx = [row.createIdx for row in cursor.fetchall()]

                    # 3. Obtener Check Constraints
                    cursor.execute(f"""
                        SELECT 
                            'ALTER TABLE [{schema}].[{table}] ' +
                            'ADD CONSTRAINT [' + cc.name + '] CHECK ' + 
                            REPLACE(REPLACE(CAST(cc.definition AS NVARCHAR(MAX)), '(', ''), ')', '') AS createConstraint
                        FROM sys.check_constraints cc
                        WHERE cc.parent_object_id = OBJECT_ID('{schema}.{table}')
                    """)
                    create_constraint = [row.createConstraint for row in cursor.fetchall()]

                    # 4. Obtener Foreign Keys
                    cursor.execute(f"""
                        SELECT 
                            'ALTER TABLE [{schema}].[{table}] ' +
                            'ADD CONSTRAINT [' + fk.name + '] FOREIGN KEY (' +
                            (
                                SELECT STRING_AGG('[' + c.name + ']', ', ')
                                FROM sys.foreign_key_columns fkc
                                JOIN sys.columns c ON fkc.parent_object_id = c.object_id AND fkc.parent_column_id = c.column_id
                                WHERE fkc.constraint_object_id = fk.object_id
                            ) + ') ' +
                            'REFERENCES [' + SCHEMA_NAME(ref_tab.schema_id) + '].[' + ref_tab.name + '] (' +
                            (
                                SELECT STRING_AGG('[' + c.name + ']', ', ')
                                FROM sys.foreign_key_columns fkc
                                JOIN sys.columns c ON fkc.referenced_object_id = c.object_id AND fkc.referenced_column_id = c.column_id
                                WHERE fkc.constraint_object_id = fk.object_id
                            ) + ')' +
                            CASE 
                                WHEN fk.delete_referential_action = 1 THEN ' ON DELETE CASCADE'
                                WHEN fk.delete_referential_action = 2 THEN ' ON DELETE SET NULL'
                                WHEN fk.delete_referential_action = 3 THEN ' ON DELETE SET DEFAULT'
                                ELSE ''
                            END +
                            CASE 
                                WHEN fk.update_referential_action = 1 THEN ' ON UPDATE CASCADE'
                                WHEN fk.update_referential_action = 2 THEN ' ON UPDATE SET NULL'
                                WHEN fk.update_referential_action = 3 THEN ' ON UPDATE SET DEFAULT'
                                ELSE ''
                            END AS createFk
                        FROM sys.foreign_keys fk
                        JOIN sys.tables ref_tab ON fk.referenced_object_id = ref_tab.object_id
                        WHERE fk.parent_object_id = OBJECT_ID('{schema}.{table}')
                    """)
                    create_fk = [row.createFk for row in cursor.fetchall()]

                except pyodbc.Error as e:
                    self.log(f"Error al obtener DDL: {str(e)}", level=logging.ERROR)
                    raise
                
                # 5. Eliminar tabla original
                self.log("Eliminando tabla original...")
                cursor.execute(f"DROP TABLE [{schema}].[{table}]")
                
                # 6. Crear nueva tabla con la columna adicional
                # Modificar el CREATE TABLE para incluir la nueva columna
                self.log("Modificando DDL para incluir nuevas columnas...")
                new_create_table = self.getNewCreateTable(create_table, columns)
                
                self.log("Creando nueva tabla con la columna(s) adicional(es)...")
                cursor.execute(new_create_table)
                
                # 7. Copiar datos de la tabla temporal
                self.log("Copiando datos desde tabla temporal...")
                
                # Obtener columnas de la tabla temporal
                cursor.execute(f"""
                    SELECT STRING_AGG(QUOTENAME(name), ', ')
                    FROM sys.columns
                    WHERE object_id = OBJECT_ID('{schema}.{table}_TEMP')
                """)
                columns_list = cursor.fetchone()[0]
                
                # Copiar datos con IDENTITY INSERT si es necesario
                cursor.execute(f"""
                    -- Verificar si la tabla tiene columnas identity
                    DECLARE @has_identity BIT = 0;
                    SELECT @has_identity = 1 
                    FROM sys.columns 
                    WHERE object_id = OBJECT_ID('{schema}.{table}') 
                    AND is_identity = 1;
                    
                    IF @has_identity = 1
                        SET IDENTITY_INSERT [{schema}].[{table}] ON;
                    
                    INSERT INTO [{schema}].[{table}] ({columns_list})
                    SELECT {columns_list}
                    FROM [{schema}].[{table}_TEMP];
                    
                    IF @has_identity = 1
                        SET IDENTITY_INSERT [{schema}].[{table}] OFF;
                """)
                
                # 8. Eliminar tabla temporal
                self.log("Eliminando tabla temporal...")
                cursor.execute(f"DROP TABLE [{schema}].[{table}_TEMP]")
                
                # 9. Recrear índices
                self.log("Recreando índices...")
                for idx_sql in create_idx:
                    cursor.execute(idx_sql)
                
                # 10. Recrear constraints CHECK
                self.log("Recreando constraints CHECK...")
                for constraint_sql in create_constraint:
                    cursor.execute(constraint_sql)
                
                # 11. Recrear FK (que la tabla referencia)
                self.log("Recreando claves foráneas...")
                for fk_sql in create_fk:
                    cursor.execute(fk_sql)
                
                # 12. Recrear FK que referencian esta tabla
                self.log("Recreando claves foráneas que referencian esta tabla...")
                for fk in referencing_fks:
                    cursor.execute(fk.create_script)
                
                # 13. Restaurar permisos
                self.log("Restaurando permisos...")
                for perm in table_permissions:
                    cursor.execute(perm.grant_script)
                
                # Confirmar transacción
                cursor.execute("COMMIT TRANSACTION")
                self.connection.commit()
                self.log("Transacción completada exitosamente")
                QMessageBox.information(self, "Éxito", f"Columna(s) agregada exitosamente a '{schema}.{table}'")
                self.multi_columns_table.setRowCount(0)
                
                # Refrescar lista de columnas
                self.load_table_columns()
                
            except Exception as e:
                cursor.execute("ROLLBACK TRANSACTION")
                self.log(f"Error durante la transacción: {str(e)} - Realizando ROLLBACK", level=logging.ERROR)
                QMessageBox.critical(self, "Error", f"Error al agregar columna: {str(e)}")
                raise
        
        except pyodbc.Error as e:
            QMessageBox.critical(self, "Error", f"Error de base de datos: {str(e)}")
            self.log(f"Error de base de datos: {str(e)}", level=logging.ERROR)
            raise
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error inesperado: {str(e)}")
            self.log(f"Error inesperado: {str(e)}", level=logging.ERROR)
            raise

class ColumnEditorDialog(QDialog):
    def __init__(self, name, col_type, nullable, default, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Editar Columna: {name}")
        
        layout = QFormLayout(self)
        
        # Nombre (no editable para renombrar usar rename_column)
        self.name_label = QLabel(name)
        layout.addRow("Nombre:", self.name_label)
        
        # Tipo de dato
        self.type_combo = QComboBox()
        types = [
            "int", "bigint", "smallint", "tinyint", "bit",
            "decimal", "numeric", "money", "smallmoney",
            "float", "real",
            "date", "datetime", "datetime2", "smalldatetime", "time",
            "char", "varchar", "text", "nchar", "nvarchar", "ntext",
            "binary", "varbinary", "image",
            "uniqueidentifier", "xml", "sql_variant"
        ]
        self.type_combo.addItems(types)
        
        # Parámetros del tipo
        self.params_input = QLineEdit()
        if '(' in col_type:
            self.params_input.setText(col_type.split('(')[1].split(')')[0])
            base_type = col_type.split('(')[0]
            self.type_combo.setCurrentText(base_type)
        else:
            self.type_combo.setCurrentText(col_type)
        
        type_layout = QHBoxLayout()
        type_layout.addWidget(self.type_combo)
        type_layout.addWidget(QLabel("Parámetros:"))
        type_layout.addWidget(self.params_input)
        layout.addRow("Tipo:", type_layout)
        
        # Nulable
        self.nullable_check = QCheckBox()
        self.nullable_check.setChecked(nullable)
        layout.addRow("Permitir NULL:", self.nullable_check)
        
        # Valor por defecto
        self.default_input = QLineEdit(default)
        layout.addRow("Valor por defecto:", self.default_input)
        
        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def get_column_data(self):
        """Devuelve los datos editados como diccionario"""
        return {
            'type': f"{self.type_combo.currentText()}({self.params_input.text()})" if self.params_input.text() else self.type_combo.currentText(),
            'nullable': self.nullable_check.isChecked(),
            'default': self.default_input.text()
        }
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SQLServerColumnAdder()
    window.show()
    sys.exit(app.exec_())