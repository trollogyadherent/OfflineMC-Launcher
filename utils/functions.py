import json
import os
import platform
import subprocess
import sys
import zipfile

from utils.config import cfg
from utils import constants as cn
from utils import logger


def read_text(path):
    if not os.path.isfile(path):
        return None
    file = open(path)
    text = file.read()  # .replace("\n", " ")
    file.close()
    return text


def mc_available(side, version):
    index_path = os.path.join(cfg.data_location, 'minecraft/version_indexes', f'{version}.json')
    assets_index_path = os.path.join(cfg.data_location, 'minecraft/versions', version, 'assets/indexes',
                                    version + '.json')
    if not os.path.isfile(index_path):
        logger.log('e', f'Could not find version index {index_path}')
        return False
    if side == 'client' and not os.path.isfile(assets_index_path):
        logger.log('e', f'Could not find asset index {assets_index_path}')
        return False

    if side == 'client':
        client_path = os.path.join(cfg.data_location, 'minecraft/versions', version, 'client', f'{version}.jar')
        if not os.path.isfile(client_path):
            logger.log('e', f'Could not find client {client_path}')
            return False
    else:
        server_path = os.path.join(cfg.data_location,
                                   'libs/libraries/net/minecraft/server', version, f'server-{version}.jar')
        if not os.path.isfile(server_path):
            logger.log('e', f'Could not find server {server_path}')
            return False

    index_data = json.loads(read_text(index_path))
    for library in index_data['libraries']:
        if 'artifact' in library['downloads']:
            lib_path = os.path.join(cfg.data_location, 'libs/libraries',
                                    library['downloads']['artifact']['path'])
            if not os.path.isfile(lib_path):
                logger.log('e', f'Could not find library {lib_path}')
                return False
        if 'classifiers' in library['downloads']:
            for key in library['downloads']['classifiers']:
                if key.startswith('natives-'):
                    native_path = os.path.join(cfg.data_location, 'libs/native',
                                               library['downloads']['classifiers'][key]['path'])
                    if not os.path.isfile(native_path):
                        logger.log('e', f'Could not find native library {native_path}')
                        return False

    assets_index_data = json.loads(read_text(assets_index_path))
    for index in assets_index_data['objects']:
        obj = assets_index_data['objects'][index]
        name = obj['hash']
        path = os.path.join(cfg.data_location, 'minecraft/versions', version, 'assets/objects', name[:2],
                            name)
        if not os.path.isfile(path):
            logger.log('e', f'Could not find asset {path}')
            return False
    if 'logging' in index_data:
        print('logging detected')
        path = os.path.join(cfg.data_location, 'minecraft/versions', version, 'assets/log_configs',
                            index_data['logging']['client']['file']['id'])
        if not os.path.isfile(path):
            logger.log('e', f'Could not find log4j configuration {path}')
            return False
    return True


def get_os():
    os_dict = {
        'Linux': 'linux',
        'Windows': 'windows',
        'Darwin': 'osx'
    }
    if platform.system() not in os_dict:
        return 'linux'
    else:
        return os_dict[platform.system()]


def get_arch():
    if platform.architecture()[0] == '64bit':
        return 'x64'
    else:
        return 'x86'


def extract_natives(version, path=cfg.natives_extraction_location, os_=get_os()):
    index_path = os.path.join(cfg.data_location, 'minecraft/version_indexes', f'{version}.json')
    index_data = json.loads(read_text(index_path))

    for library in index_data['libraries']:
        if 'classifiers' in library['downloads']:
            for key in library['downloads']['classifiers']:
                if key == f'natives-{os_}':
                    lib_path = os.path.join(cfg.data_location, 'libs/native', library['downloads']['classifiers'][f'natives-{os_}']['path'])
                    with zipfile.ZipFile(lib_path, 'r') as zip_ref:
                        zip_ref.extractall(path)


def get_mc_library_paths(version, final_data=cfg.data_location, os_=get_os()):
    libs = []
    index_path = os.path.join(final_data, 'minecraft/version_indexes', f'{version}.json')
    index_data = json.loads(read_text(index_path))
    for lib in index_data['libraries']:
        if 'artifact' not in lib['downloads'] or 'classifiers' in lib['downloads']:
            continue
        if 'rules' not in lib:
            path = os.path.join(final_data, 'libs/libraries', lib['downloads']['artifact']['path'])
            libs.append(path)
        else:
            allowed = True
            for rule in lib['rules']:
                if rule['action'] == 'allow' and 'os' in rule and rule['os']['name'] != os_:
                    allowed = False
                if rule['action'] == 'disallow' and 'os' not in rule:
                    allowed = False
            if allowed:
                path = os.path.join(final_data, 'libs/libraries', lib['downloads']['artifact']['path'])
                libs.append(path)
    libs.append(os.path.join(final_data, "minecraft/versions", version, "client", version + ".jar"))
    return libs


def get_mc_args(side, version, instance_location=None, username=None, user_java_args=None, user_properties=None,
                resolution=None, final_data=cfg.data_location, os_=get_os(), os_version=platform.version(),
                arch=get_arch()):
    instance_location_ = '"' + cfg.default_client_instance_location + '"'
    if side == 'server':
        print('SERVER SNEED')
        instance_location_ = cfg.default_server_instance_location
    if instance_location:
        instance_location_ = instance_location
    resolution_ = cfg.resolution
    if resolution:
        resolution_ = resolution
    username_ = cfg.username
    if username:
        username_ = username
    user_properties_ = cfg.user_properties
    if user_properties:
        user_properties_ = user_properties

    arguments = []
    index_path = os.path.join(final_data, 'minecraft/version_indexes', f'{version}.json')
    index_data = json.loads(read_text(index_path))

    arg_data = {
        'auth_player_name': username_,
        'version_name': version,
        'game_directory': instance_location_,
        'assets_root': '"' + os.path.join(final_data, 'minecraft/versions', version, 'assets') + '"',
        'assets_index_name': version,
        'auth_access_token': '""',
        'auth_uuid': '""',
        'user_type': '""',
        'user_properties': user_properties_,
        'resolution_width': resolution_.split('x')[0],
        'resolution_height': resolution_.split('x')[1],
        'clientid': '""',
        'auth_xuid': '""',
        'version_type': '""'
    }

    # Java executable
    jversion_dict = {
        'java-runtime-beta': '17',
        'java-runtime-alph': '16',
        'jre-legacy': '8'
    }
    if 'javaVersion' not in index_data:
        jversion = '8'
    else:
        jversion = jversion_dict[index_data['javaVersion']['component']]
    if cfg.java_path[jversion][os_] == '':
        sys.exit(f'No Java set for Java {jversion} for the platform {os_}')

    arguments.append(cfg.java_path[jversion][os_])

    # Log4j mitigation
    if 'logging' in index_data:
        log4j_conf_name = index_data['logging']['client']['file']['id']
        log4j_conf_path = os.path.join(cfg.data_location,
                                       'minecraft/versions', version, 'assets/log_configs', log4j_conf_name)
        log4j_arg = f'"-Dlog4j.configurationFile={log4j_conf_path}"'
        arguments.append(log4j_arg)

    # Legacy natives path
    if 'arguments' not in index_data:
        natives_arg = f'"-Djava.library.path={cfg.natives_extraction_location}"'
        arguments.append(natives_arg)

    # Legacy java arguments
    if 'arguments' not in index_data:
        # Client jar
        if side == 'client':
            client_jar_arg = f'"-Dminecraft.client.jar={os.path.join(final_data, "minecraft/versions", version, "client", version + ".jar")}"'
            arguments.append(client_jar_arg)

        # Classpath
        arguments.append('-cp')  # ( ͡° ͜ʖ ͡°)
        libs = get_mc_library_paths(version, final_data, os_)
        if len(libs) == 0:
            sys.exit('Something went wrong while getting libraries paths')
        arguments.append('"' + ';'.join(libs) + '"')

        # Log location
        arguments.append(f'"-Dlog.dir={os.path.join(instance_location_[1:-1], "logs")}"')

        # Other args (not necessary f9or game to start)
        if os_ == 'windows':
            arguments.append('"-XX:HeapDumpPath=MojangTricksIntelDriversForPerformance_javaw.exe_minecraft.exe.heapdump"')

        if os_ == 'windows' and os_version.startswith('10'):
            arguments.append('"-Dos.name=Windows 10"')
            arguments.append('"-Dos.version=10.0"')

    # Recent version jvm arguments
    else:
        libs = get_mc_library_paths(version, final_data)
        if len(libs) == 0:
            sys.exit('Something went wrong while getting libraries paths')
        cp = ';'.join(libs)

        jvm_arg_data = {
            'natives_directory': cfg.natives_extraction_location,
            'launcher_name': cn.LAUNCHER_NAME,
            'launcher_version': cn.LAUNCHER_VERSION,
            'classpath': cp
        }

        for argument in index_data['arguments']['jvm']:
            if 'rules' in argument:
                for rule in argument['rules']:
                    if rule['action'] == 'allow':
                        if 'os' in rule:
                            def add_rule_arg():
                                # TO TEST
                                for value in argument['value']:
                                    arg_ = value
                                    for key_ in jvm_arg_data:
                                        arg_ = '"' + value.replace('${' + key_ + '}', jvm_arg_data[key_]) + '"'
                                    arguments.append(arg_)
                            if 'name' in rule['os']:
                                if 'version' in rule['os'] and os_ == 'windows' and rule['os']['name'] == 'windows' and rule['os']['version'] == '^10\\.' and platform.version().startswith('10'):
                                    add_rule_arg()
                                elif 'version' in rule['os'] and rule['os']['name'] == os_:
                                    add_rule_arg()
                            elif 'arch' in rule['os'] and rule['os']['arch'] == arch:
                                add_rule_arg()
            else:
                arg = argument
                for key in jvm_arg_data:
                    arg = arg.replace('${' + key + '}', jvm_arg_data[key])
                arguments.append('"' + arg + '"')

    # User args
    user_java_args_ = cfg.user_java_args
    if user_java_args:
        user_java_args_ = user_java_args
    arguments.append(user_java_args_)

    # Main class
    if side == 'client':
        arguments.append(index_data['mainClass'])
    else:
        arguments.append(os.path.join(final_data, "libs/libraries/net/minecraft/server", version, "client", "server-" + version + ".jar"))

    # Legacy Minecraft arguments
    if 'arguments' not in index_data:
        if side == 'client':
            mc_arg_string = index_data['minecraftArguments']

            for key in arg_data:
                mc_arg_string = mc_arg_string.replace('${' + key + '}', arg_data[key])

            arguments.append(mc_arg_string)

    # Recent Minecraft arguments
    else:

        rule_features = {
            'is_demo_user': False,
            'has_custom_resolution': True
        }

        mcargs_temp = []

        for argument in index_data['arguments']['game']:
            if 'rules' in argument:
                checks_all_features = True
                for rule in argument['rules']:
                    if rule['action'] == 'allow':
                        for key in rule['features']:
                            if key not in rule_features:
                                logger.log('w', f'Unknown feature "{key}"')
                                checks_all_features = False
                                continue
                            if not rule_features[key]:
                                checks_all_features = False
                if checks_all_features:
                    mcargs_temp += argument['value']
            else:
                mcargs_temp.append(argument)

        mcargs_replaced = []

        for arg in mcargs_temp:
            arg_ = arg
            for key in arg_data:
                arg_ = arg_.replace('${' + key + '}', arg_data[key])
            mcargs_replaced.append(arg_)

        arguments += mcargs_replaced

    if len(arguments) == 0:
        sys.exit(f'Error while generating arguments')
    else:
        os_fixed_args = []
        for arg in arguments:
            if os_ == 'windows':
                arg = arg.replace('/', '\\')
                os_fixed_args.append(arg)
            else:
                arg = arg.replace('\\', '/')
                os_fixed_args.append(arg)
        print(' '.join(os_fixed_args))
        return arguments


def launch_vanilla(side, version):
    if side == 'client':
        extract_natives(version)
    args = get_mc_args(side, version)
    command = ' '.join(args)
    # subprocess.call(args)
    subprocess.run(command) #Popen(command)
