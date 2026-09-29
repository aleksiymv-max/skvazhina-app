from pathlib import Path
root=Path.cwd()
for p in root.glob('lib/**/*.dart'):
 x=p.read_text()
 if 'ExpansionTile' in x and 'initiallyExpanded:true' in x:
  x=x.replace('initiallyExpanded:true','initiallyExpanded:false')
  p.write_text(x)
