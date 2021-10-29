# -*- mode: python ; coding: utf-8 -*-

import os
block_cipher = None


a = Analysis([os.getcwd() + '\\..\\Plot_Bot.py'],
             pathex=[os.getcwd() + '\\..\\'],
             binaries=[],
             datas=[('C:\\Users\\mfpeyfuss\\AppData\\Local\\Programs\\Python\\Python39\\Lib\\site-packages\\plotly\\', 'plotly')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          Tree(os.getcwd() + "\\..\\Icons", prefix="Icons"),
          Tree(os.getcwd() + "\\..\\Documents", prefix="Documents"),
          a.zipfiles,
          a.datas,
          [],
          name='Plot bootloader_ignore_signals',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon=os.getcwd() + '\\..\\Icons\\plot_bot.ico')
