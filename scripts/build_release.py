"""Validate the local skill and build a deterministic release ZIP (stdlib only)."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 't18d-8255-debug'

def validate():
    text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    match = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if not match:
        raise ValueError('Missing skill frontmatter')
    fields = dict(line.split(': ', 1) for line in match[1].splitlines())
    if fields.get('name') != SKILL.name or not fields.get('description'):
        raise ValueError('Invalid skill name/description')
    if set(fields) != {'name', 'description'} or len(fields['description']) > 1024:
        raise ValueError('Unexpected frontmatter schema')
    ui = (SKILL / 'agents/openai.yaml').read_text(encoding='utf-8').splitlines()
    if ui[0] != 'interface:':
        raise ValueError('Invalid interface metadata')
    values = {}
    for line in ui[1:]:
        key, value = line.strip().split(': ', 1)
        values[key] = json.loads(value)
    if not 25 <= len(values['short_description']) <= 64 or '$' + SKILL.name not in values['default_prompt']:
        raise ValueError('Invalid UI metadata values')
    files = sorted(path for path in SKILL.rglob('*') if path.is_file())
    expected = {'SKILL.md', 'agents/openai.yaml', 'scripts/editor_line_locator.py', 'references/history.md', 'references/log-map.md', 'references/diagnosis.md', 'references/report-template.md', 'references/time-alignment.md'}
    if {path.relative_to(SKILL).as_posix() for path in files} != expected:
        raise ValueError('Missing or unexpected skill files')
    for path in files:
        text = path.read_text(encoding='utf-8')
        if '[TODO:' in text:
            raise ValueError('Unfinished scaffold: ' + str(path))
        if path.suffix == '.md':
            for target in re.findall(r'\]\(([^)]+)\)', text):
                if '://' in target:
                    continue
                linked = (path.parent / target).resolve()
                if not linked.is_relative_to(SKILL) or not linked.is_file():
                    raise ValueError('Invalid internal link: ' + target)
        if path.suffix == '.py':
            compile(text, str(path), 'exec')
    return files

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'dist')
    args = parser.parse_args()
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('VERSION must be x.y.z')
    files = validate()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    archive = args.output_dir / f'{SKILL.name}-v{version}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, path.read_bytes())
    with zipfile.ZipFile(archive) as output:
        if output.testzip() or len(output.namelist()) != len(files):
            raise ValueError('ZIP integrity failed')
        for path in files:
            if output.read(path.relative_to(ROOT).as_posix()) != path.read_bytes():
                raise ValueError('ZIP content mismatch')
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (args.output_dir / 'SHA256SUMS').write_text(f'{digest}  {archive.name}\n', encoding='utf-8', newline='\n')
    print(f'Validated {len(files)} skill files; built {archive.name}')
    print(f'SHA256 {digest}')

if __name__ == '__main__':
    main()
