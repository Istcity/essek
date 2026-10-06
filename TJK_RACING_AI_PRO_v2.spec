import os

frontend_datas = []
for root, dirs, files in os.walk('frontend'):
    for f in files:
        if not f.endswith('.zip') and not f.endswith('.exe'):
            rel_dir = os.path.relpath(root, '.')
            frontend_datas.append((os.path.join(root, f), rel_dir))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=frontend_datas + [('backend', 'backend'), ('data', 'data')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='TJK_RACING_AI_PRO_v2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
