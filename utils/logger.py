import os.path
from datetime import datetime

from utils.config import cfg


time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")


# https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
def log(severity, text):
    color_end = '\033[0m'
    severity_dict = {'i': 'Info', 's': 'Sneed', 'w': 'Warning', 'e': 'Error'}
    severity_color = {'i': '', 's': '\033[92m', 'w': '\033[93m', 'e': '\033[91m'}
    os.makedirs(cfg.logs_location, exist_ok=True)
    with open(os.path.join(cfg.logs_location, f'log_{time}.log'), 'a+') as lf:
        print(
            f'[{severity_color[severity.lower()]}{severity_dict[severity.lower()]}{color_end}] {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}: {text}')
        lf.write(f'[{severity_dict[severity.lower()]}] {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}: {text}\n')
