import argparse
import glob
import os
from typing import List, Tuple
from YEDDA_Annotator import YeddaFrame
import datetime
import re

TXT_EXT = '.txt'
ANN_EXT = '.ann'
EXTRACTED_DIR_BASE = 'extracted_text'
FILE_SEPARATOR = '''

----------------------------

'''


class TaggedFile:
    def __init__(self, file_name):
        self.file_name: str = file_name
        self.found_tagged: bool = True
        self._untagged_text, self.tagged_text = self.read_files()

    def read_files(self) -> Tuple[str, str]:
        with open(self.file_name, 'r') as f:
            ut = f.read()
        try:
            with open(self.annotated_file, 'r') as f:
                tt = f.read()
        except FileNotFoundError:
            self.found_tagged = False
            tt = ut
        return ut, tt

    @property
    def untagged_text(self) -> str:
        return self._untagged_text

    @property
    def annotated_file(self) -> str:
        return self.file_name + ANN_EXT

    def list_all_tags(self) -> List[str]:
        # print("Finding all tags in " + self.annotated_file)
        matches = YeddaFrame.tag_regex.findall(self.tagged_text)
        tags = [m[0] for m in matches]
        return tags

    def get_text_for_tag(self, tag: str) -> List[str]:
        tag_regex = re.compile('<' + tag + '>(.*?)</' + tag + '>')
        matches = tag_regex.findall(self.tagged_text)
        matches = [re.sub('<[\w/-]+?>', '', m) for m in matches]
        return matches


def get_timestamp() -> str:
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def make_extracted_dir(path: str) -> str:
    dir_path = os.path.join(path, EXTRACTED_DIR_BASE + '_' + get_timestamp())
    os.makedirs(dir_path)
    return dir_path


def process_directory(path: str) -> None:
    files = get_files(path)
    # print(files)
    tags = find_all_tags(files)
    print('Found tags: ' + str(tags))

    if not tags:
        print('No tags found. Exiting')
        return

    ext_dir = make_extracted_dir(path)

    for tag in tags:
        text_for_tag = [[file.file_name] + file.get_text_for_tag(tag) for file in files]
        file_strs = ['\n\n'.join(l) for l in text_for_tag]
        str_to_write = FILE_SEPARATOR.join(file_strs)
        with open(os.path.join(ext_dir, tag + TXT_EXT), 'w') as f:
            f.write(str_to_write)


def get_files(path):
    txt_file_names = glob.glob(path + os.sep + '*' + TXT_EXT)
    files = [TaggedFile(fn) for fn in txt_file_names]
    return files


def find_all_tags(files):
    tags = []
    for file in files:
        tags.extend(file.list_all_tags())
    tags = list(set(tags))  # remove duplicated elements by casting to set
    tags.sort()
    return tags


def main():
    print("Tagged file processor")
    parser = argparse.ArgumentParser(description='Extract the tagged text from a folder of files and create new files')
    parser.add_argument('path',
                        help='The directory to process')
    # parser.add_argument('-16', '--16bit-pngs', dest='sixteen_bit_pngs', action='store_const',
    #                     const=True, default=False,
    #                     help='Save as 16 bit PNGs (default: False)')
    # parser.add_argument('--no-thumbnails', action='store_const',
    #                     const=True, default=False,
    #                     help='Skip making thumbnails (default: False)')
    # parser.add_argument('--no-pngs', action='store_const',
    #                     const=True, default=False,
    #                     help='Skip making PNG files (default: False)')
    # parser.add_argument('-f', '--format', choices=['png', 'jpg'], default='png',
    #                     help='Format of files to save. Only PNG of JPG are supported at the moment')

    args = parser.parse_args()
    print('Processing files from: ' + args.path)

    process_directory(args.path)

if __name__ == '__main__':
    main()
