# Requeriments python in client
# Linux with freetds
sudo apt-get install -y freetds-dev freetds-bin tdsodbc

# Navigate to folder to pyenv an run commands
python3 -m venv pyenv
source pyenv/bin/activate

# Run command in new instance

# Instalar paquetes
pip install pyqt5 pyodbc

# Instalar devtools compiler
pip install pyinstaller

pyinstaller --onefile\
            --windowed\
            --name "SQLServer Column Adder"\
            --icon=assets/icon.ico\
            --add-data "sql_column_adder.log:."\
            --hidden-import PyQt5.QtWidgets\
            --hidden-import pyodbc\
            main.py
