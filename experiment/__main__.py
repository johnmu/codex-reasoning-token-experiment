"""One entry point for offline analysis and explicitly requested live collection."""
import argparse
import runpy
import sys
from pathlib import Path

COMMANDS = {
    'verify': ('public_audit', 'Check the included datasets, or a specified public dataset'),
    'analyze': ('analyze_followup', 'Regenerate the follow-up and pooled accuracy results'),
    'analyze-study': ('analyze', 'Analyze one study; defaults to the initial study'),
    'setup': ('setup', 'Prepare isolated homes or sign in'),
    'run': ('run', 'Preview a collection; --execute makes model calls'),
    'audit': ('audit', 'Audit private raw captures'),
    'summarize': ('summarize', 'Summarize private raw captures'),
    'export': ('export_public', 'Export audited captures into a public dataset'),
    'check-public': ('check_public', 'Scan tracked or staged files for private information'),
}


def main():
    description = '\n'.join(f'  {name:15} {details[1]}' for name, details in COMMANDS.items())
    parser = argparse.ArgumentParser(description=__doc__, epilog=description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('command', choices=COMMANDS)
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help']:
        parser.print_help()
        return
    command = sys.argv[1]
    if command not in COMMANDS:
        parser.error(f'unknown command: {command}')
    source = Path(__file__).with_name('src')
    sys.path.insert(0, str(source))
    script = source / f'{COMMANDS[command][0]}.py'
    sys.argv = [str(script), *sys.argv[2:]]
    runpy.run_path(str(script), run_name='__main__')


if __name__ == '__main__':
    main()
