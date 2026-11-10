#!/usr/bin/env python3
"""Build Snapper Assist as a native, non-activating macOS selection utility."""
import argparse
from pathlib import Path
import plistlib
import shutil
import subprocess

root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path,default=Path.home()/'Applications/Snapper Assist.app')
parser.add_argument('--preview-bundle',action='store_true',help='Use an isolated preview identity; never request AX permission for it')
args=parser.parse_args()
cache=root/'.runtime/native-build'/('preview' if args.preview_bundle else 'release');cache.mkdir(parents=True,exist_ok=True)
binary=cache/'SnapperAssist'
subprocess.run(['swiftc','-O','-framework','AppKit','-framework','ApplicationServices','-framework','FoundationModels',*[str(root/'native'/name) for name in ['SelectionCore.swift','PromptPreparation.swift','DomainMethods.swift','DomainMethodTests.swift','RefinementLaunch.swift','SelectionTests.swift','SelectionAssistant.swift']],'-o',str(binary)],check=True)
subprocess.run([str(binary),'--self-test'],check=True)
subprocess.run(['swift',str(root/'native/render-icons.swift'),str(cache/'icons')],check=True)
icon=cache/'SnapperAssist.icns'
subprocess.run(['/usr/bin/iconutil','-c','icns',str(cache/'icons/snapper-assist.iconset'),'-o',str(icon)],check=True)
target=args.output.expanduser().resolve()
if target.exists():
    existing=target/'Contents/Info.plist'
    if not existing.exists() or plistlib.loads(existing.read_bytes()).get('CFBundleIdentifier') not in ['local.snapper.assist','local.snapper.assist.preview']:
        raise RuntimeError('Refusing to replace unrelated app')
    shutil.rmtree(target)
mac=target/'Contents/MacOS';resources=target/'Contents/Resources';mac.mkdir(parents=True);resources.mkdir(parents=True)
shutil.copy2(binary,mac/'SnapperAssist');shutil.copy2(icon,resources/'SnapperAssist.icns');shutil.copy2(root/'knowledge.json',resources/'knowledge.json')
subprocess.run(['python3',str(root.parent/'scripts/package_methods.py'),'--output',str(resources)],check=True)
info={'CFBundleName':'Snapper Assist','CFBundleDisplayName':'Snapper Assist','CFBundleIdentifier':'local.snapper.assist','CFBundleExecutable':'SnapperAssist','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.8.0','CFBundleVersion':'11','CFBundleIconFile':'SnapperAssist.icns','LSMinimumSystemVersion':'26.0','LSUIElement':True,'NSHighResolutionCapable':True,'NSPrincipalClass':'NSApplication','NSAccessibilityUsageDescription':'读取当前软件中你主动选中的文字，显示不抢焦点的浮条；你点击应用后才替换选区。','NSServices':[{'NSMenuItem':{'default':'Snapper Assist · 整理选文'},'NSMessage':'optimizeSelection','NSPortName':'Snapper Assist','NSSendTypes':['NSStringPboardType','public.utf8-plain-text'],'NSRequiredContext':{'NSTextContext':'NSInputText'}}]}
if args.preview_bundle:
    info.update(CFBundleIdentifier='local.snapper.assist.preview',CFBundleName='Snapper Assist Preview',CFBundleDisplayName='Snapper Assist Preview',NSServices=[])
(target/'Contents/Info.plist').write_bytes(plistlib.dumps(info))
subprocess.run(['/usr/bin/xattr','-cr',str(target)],check=True)
subprocess.run(['/usr/bin/codesign','--force','--deep','--sign','-',str(target)],check=True,capture_output=True)
subprocess.run([str(mac/'SnapperAssist'),'--check-bundled-methods'],check=True)
print(target)
