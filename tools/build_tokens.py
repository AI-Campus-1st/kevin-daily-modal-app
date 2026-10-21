'''DESIGN.md 머리말 → frontend/css/tokens.css 생성 (tech_stack.md 5장)

- docs/design/DESIGN.md 맨 위 '---' 사이의 머리말(YAML)을 PyYAML로 읽음
- colors, typography, rounded, spacing, elevation, layout을 CSS 변수로 만듦
  - components는 CSS 변수로 만들지 않음
  - 이름: 머리말 경로를 '-'로 잇고 낮은 카멜 표기를 '-' 표기로 바꿈
    (예: typography.body.fontSize → --typography-body-font-size)
  - 값 안의 {colors.primary} 같은 참조는 var(--colors-primary)로 바꿈
- --check: 파일을 쓰지 않고 지금 tokens.css가 머리말과 같은지만 확인. 다르면 종료 코드 1

실행 예 (backend/ 폴더에서, PyYAML이 설치된 가상 환경 사용)
    .venv\\Scripts\\python ..\\tools\\build_tokens.py
    .venv\\Scripts\\python ..\\tools\\build_tokens.py --check
'''

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DESIGN_PATH = ROOT / 'docs' / 'design' / 'DESIGN.md'
TOKENS_PATH = ROOT / 'frontend' / 'css' / 'tokens.css'

GROUPS = ('colors', 'typography', 'rounded', 'spacing', 'elevation', 'layout')
REFERENCE = re.compile(r'\{([a-zA-Z0-9_.-]+)\}')

HEADER = '''/* DESIGN.md 머리말에서 생성한 파일. 직접 수정 금지
 * 원본: docs/design/DESIGN.md
 * 생성: backend/ 폴더에서 .venv\\Scripts\\python ..\\tools\\build_tokens.py
 */
'''


class TokenError(Exception):
    '''머리말 형식 오류 또는 없는 토큰 참조'''


def read_front_matter(path):
    '''문서 맨 위 '---' 사이의 YAML을 딕셔너리로 읽음'''
    lines = path.read_text(encoding='utf-8').splitlines()
    if not lines or lines[0].strip() != '---':
        raise TokenError('머리말 시작(---) 없음')
    for index in range(1, len(lines)):
        if lines[index].strip() == '---':
            data = yaml.safe_load('\n'.join(lines[1:index]))
            if not isinstance(data, dict):
                raise TokenError('머리말이 키-값 형식이 아님')
            return data
    raise TokenError('머리말 끝(---) 없음')


def kebab(name):
    '''낮은 카멜 표기를 '-' 표기로 바꿈 (fontSize → font-size)'''
    return re.sub(r'(?<=[a-z0-9])([A-Z])', r'-\1', str(name)).lower()


def variable_name(path):
    '''머리말 경로 목록 → CSS 변수 이름 (['colors', 'primary'] → --colors-primary)'''
    return '--' + '-'.join(kebab(part) for part in path)


def flatten(value, path):
    '''중첩된 딕셔너리를 (경로 목록, 값) 목록으로 펼침'''
    if isinstance(value, dict):
        items = []
        for key, child in value.items():
            items.extend(flatten(child, [*path, key]))
        return items
    return [(path, value)]


def css_value(value):
    '''YAML 값 → CSS 값 문자열'''
    if isinstance(value, bool) or value is None:
        raise TokenError(f'CSS 값으로 바꿀 수 없는 값: {value!r}')
    return str(value)


def build_css(data):
    '''머리말 딕셔너리 → tokens.css 내용'''
    entries = []
    for group in GROUPS:
        if group not in data:
            raise TokenError(f'머리말에 {group} 없음')
        for path, value in flatten(data[group], [group]):
            entries.append((variable_name(path), css_value(value), group))

    names = {name for name, _, _ in entries}

    def replace(match):
        name = variable_name(match.group(1).split('.'))
        if name not in names:
            raise TokenError(f'없는 토큰 참조: {{{match.group(1)}}}')
        return f'var({name})'

    lines = [HEADER, ':root {']
    current = None
    for name, value, group in entries:
        if group != current:
            if current is not None:
                lines.append('')
            lines.append(f'  /* {group} */')
            current = group
        lines.append(f'  {name}: {REFERENCE.sub(replace, value)};')
    lines.append('}')
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description='DESIGN.md 머리말로 tokens.css 생성')
    parser.add_argument('--check', action='store_true', help='쓰지 않고 일치 여부만 확인')
    args = parser.parse_args()

    try:
        css = build_css(read_front_matter(DESIGN_PATH))
    except (TokenError, yaml.YAMLError) as error:
        print(f'오류: {error}', file=sys.stderr)
        return 1

    if args.check:
        current = TOKENS_PATH.read_text(encoding='utf-8') if TOKENS_PATH.exists() else None
        if current != css:
            message = 'tokens.css가 DESIGN.md 머리말과 다름. build_tokens.py를 다시 실행'
            print(message, file=sys.stderr)
            return 1
        print('tokens.css가 DESIGN.md 머리말과 같음')
        return 0

    TOKENS_PATH.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_PATH.write_text(css, encoding='utf-8', newline='\n')
    print(f'생성: {TOKENS_PATH.relative_to(ROOT).as_posix()}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
