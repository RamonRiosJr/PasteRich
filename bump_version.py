import sys
import re
import subprocess

def run(cmd):
    subprocess.run(cmd, check=True, shell=True)

def main():
    if len(sys.argv) < 2:
        print("Usage: python bump_version.py <version> (e.g. 1.2.1)")
        sys.exit(1)
        
    version = sys.argv[1].lstrip('v')
    
    print(f"Bumping version to {version}...")
    
    # 1. Update pasterich.py
    with open('pasterich.py', 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'__version__ = ".*?"', f'__version__ = "{version}"', content)
    with open('pasterich.py', 'w', encoding='utf-8') as f:
        f.write(content)
        
    # 2. Update README.md
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # If there's no version badge, add it
    if 'badge/version-' not in content:
        content = content.replace('[![Platform]', f'[![Version](https://img.shields.io/badge/version-{version}-blue.svg)](#)\n  [![Platform]')
    else:
        content = re.sub(r'badge/version-.*?-blue', f'badge/version-{version}-blue', content)
        
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(content)
        
    # 3. Commit and tag
    run('git add pasterich.py README.md')
    run(f'git commit -m "chore: Bump version to {version}"')
    run(f'git tag v{version}')
    
    print(f"\nVersion successfully bumped to {version}!")
    print("To trigger the auto-update and release on GitHub, simply push your tags:")
    print("    git push origin master --tags")

if __name__ == '__main__':
    main()
