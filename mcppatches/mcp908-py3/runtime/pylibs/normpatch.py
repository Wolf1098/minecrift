import sys
import os
import shutil
from optparse import OptionParser


def normalisepatch(in_filename, out_filename=None):
    in_filename = os.path.normpath(in_filename)
    if out_filename is None:
        tmp_filename = in_filename + '.tmp'
    else:
        out_filename = os.path.normpath(out_filename)
        tmp_filename = out_filename
        dir_name = os.path.dirname(out_filename)
        if dir_name:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
    with open(in_filename, 'rb') as inpatch:
        with open(tmp_filename, 'wb') as outpatch:
            for line in inpatch:
                line = line.rstrip(b'\r\n')
                if line[:3] in [b'+++', b'---', b'Onl', b'dif']:
                    outpatch.write(line.replace(b'\\', os.sep.encode()).replace(b'/', os.sep.encode()) + os.linesep.encode())
                else:
                    outpatch.write(line + os.linesep.encode())
    if out_filename is None:
        shutil.move(tmp_filename, in_filename)


def main():
    usage = 'usage: %prog [options] src_file [dest_file]'
    version = '%prog 6.0'
    parser = OptionParser(version=version, usage=usage)
    options, args = parser.parse_args()
    if len(args) == 1:
        in_file = args[0]
        out_file = None
    elif len(args) == 2:
        in_file = args[0]
        out_file = args[1]
    else:
        print('src_file required', file=sys.stderr)
        sys.exit(1)
    normalisepatch(in_file, out_file)


if __name__ == '__main__':
    main()
