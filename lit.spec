# -*- mode: python -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# Собираем данные, включая статические файлы из пакета lit
datas = collect_data_files('lit')
# Добавляем pyproject.toml в корневую директорию сборки
datas.append(('pyproject.toml', '.'))

a = Analysis(
    ['lit.py'],  # Путь к главному файлу
    pathex=[],
    binaries=[],
    datas=datas,  # Передаём собранные данные
    hiddenimports=[],  # Скрытые зависимости
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],  # Исключить ненужные модули
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='lit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Сжатие бинарника
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Для консольных приложений
    onefile=True,  # Собираем в один файл
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)