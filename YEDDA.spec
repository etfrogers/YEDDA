# -*- mode: python -*-

block_cipher = None


ext_a = Analysis(['extract_tagged_text.py'],
             pathex=['C:\\Users\\Ed\\Documents\\Work\\YEDDA'],
             binaries=[],
             datas=[('version.txt', 'version.txt')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

yedda_a = Analysis(['YEDDA_Annotator.py'],
             pathex=['C:\\Users\\Ed\\Documents\\Work\\YEDDA'],
             binaries=[],
             datas=[('version.txt', 'version.txt')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

MERGE( (yedda_a, 'YEDDA_Annotator', 'YEDDA_Annotator'), (ext_a, 'extract_tagged_text', 'extract_tagged_text') )

pyz = PYZ(ext_a.pure, ext_a.zipped_data,
             cipher=block_cipher)

pyz = PYZ(yedda_a.pure, yedda_a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          yedda_a.scripts,
          yedda_a.binaries,
          yedda_a.zipfiles,
          yedda_a.datas,
          name='YEDDA_Annotator',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )

exe = EXE(pyz,
          ext_a.scripts,
          ext_a.binaries,
          ext_a.zipfiles,
          ext_a.datas,
          name='extract_tagged_text',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=True )
