import argparse
import sys
import textwrap

import utils.logger as logger
import utils.functions as fn


def main():
    parser = argparse.ArgumentParser(
        description='Minecraft launcher with modloader support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            '''Examples:
			offlinemc.py --version 1.7.10 --directory my_minecraft --forge 10.13.4.1614 --liteloader latest
			offlinemc.py --list minecraft
			offlinemc.py --list --version 1.12.2 --forge
			offlinemc.py --version 1.17 --forge latest --bake
			offlinemc.py --version 1.17 --forge latest --bake --bakejava --bakeplatform all
			'''
        )
    )
    parser.add_argument('-v', '--version', help='Minecraft version')
    parser.add_argument('-d', '--directory', help='Override config instance or server directory')
    parser.add_argument('-s', '--server', help='Launch server instead of a client', action='store_true')
    parser.add_argument('--forge', help='Forge version (may be "latest")')
    parser.add_argument('--fabric', help='Fabric version (may be "latest")')
    parser.add_argument('--liteloader', help='Liteloader version (may be "latest")')
    parser.add_argument('-a', '--arguments', nargs='*', help='Additional java arguments')
    parser.add_argument('-r', '--resolution', help='Override config resolution. Example: 800x600')
    parser.add_argument('-l', '--list', help='Lists available Minecraft or modloader versions')
    parser.add_argument('-b', '--bake', default='Baked', help='Export all files necessary for that configuration to run, and create appropriate launch scripts')
    parser.add_argument('--bakejava', help='Include java executables in baking')
    parser.add_argument('--bakeos', help='What os natives, java executables to copy, and launch scripts to create')
    parser.add_argument('-j', '--java', help='Override config java path')
    parser.add_argument('-u', '--username', help='Override config username')
    parser.add_argument('--data', help='Override config data location')
    parser.add_argument('--logs', help='Override config logs location')

    args = parser.parse_args()

    nc = OfflineMC(args)
    nc.run()


class OfflineMC:
    def __init__(self, args):
        self.args = args

    def run(self):
        logger.log('s', '#-------------------------------#')
        logger.log('s', '#---- Welcome to OfflineMC! ----#')
        logger.log('s', '#-------------------------------#')

        if not self.args.list and not self.args.version:
            sys.exit('Specify a Minecraft version, or list Minecraft or modloader versions')
        if self.args.server and not self.args.version:
            sys.exit('Specify a Minecraft version')
        if self.args.fabric and self.args.forge:
            sys.exit('You cannot run Fabric alongside Forge')
        if self.args.liteloader and self.args.server:
            sys.exit('Liteloader is a client only modloader')

        if self.args.version and not self.args.forge and not self.args.liteloader and not self.args.fabric:
            side = 'client'
            if self.args.server:
                side = 'server'
            if fn.mc_available(side, self.args.version):
                self.run_vanilla(side)
            else:
                sys.exit(f'Version {self.args.version} not installed!')

    def run_vanilla(self, side):
        fn.launch_vanilla(side, self.args.version)

    def run_forge(self, side):
        pass

    def run_liteloader(self):
        pass

    def run_forge_liteloader(self):
        pass

    def run_fabric(self, side):
        pass


if __name__ == '__main__':
    main()
