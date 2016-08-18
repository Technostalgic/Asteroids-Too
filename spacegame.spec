# -*- mode: python -*-

block_cipher = None
debug = True

added_files = [
			 ("C:\\Users\\Isaiah\\Documents\\Software Development\\GameDev\\Python\\Asteroids Too\\Graphics\\*.png",'Graphics'),
			 ("C:\\Users\\Isaiah\\Documents\\Software Development\\GameDev\\Python\\Asteroids Too\\Sounds\\*.wav",'Sounds'),
			 ("C:\\Users\\Isaiah\\Documents\\Software Development\\GameDev\\Python\\Asteroids Too\\README.txt", '.'),
			 ("C:\\Users\\Isaiah\\Documents\\Software Development\\GameDev\\Python\\Asteroids Too\\font.ttf", '.'),
			 ("C:\\Users\\Isaiah\\Documents\\Software Development\\GameDev\\Python\\Asteroids Too\\scores", '.')
			 ]

a = Analysis(['C:\\Users\\Isaiah\\Documents\\Software Development\\GameDev\\Python\\Asteroids Too\\spacegame.py'],
             pathex=['C:\\Users\\Isaiah\\AppData\\Local\\Programs\\Python\\Python35-32\\Scripts'],
             binaries=None,
             datas=added_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          #exclude_binaries=True,
          name='spacegame',
          debug=False,
          strip=False,
          #upx=True,
          console=True )

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='spacegame')
