import argparse
import glob
import os
from typing import List, Tuple, Set
from YEDDA_Annotator import YeddaFrame
import datetime
import regex as re

TXT_EXT = 'txt'
ANN_EXT = 'ann'
EXTRACTED_DIR_BASE = 'extracted_text'
FILE_SEPARATOR = '''

----------------------------

'''


class TaggedFile:
    def __init__(self, file_name: str):
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
        return f'{self.file_name}.{ANN_EXT}'

    def list_all_tags(self) -> Set[str]:
        # print("Finding all tags in " + self.annotated_file)
        matches = YeddaFrame.tag_regex.findall(self.tagged_text, overlapped=True)
        tags = {m[0] for m in matches}
        return tags

    def get_text_for_tag(self, tag: str) -> List[str]:
        tag_regex = re.compile('<' + tag + '>(.*?)</' + tag + '>', flags=re.DOTALL)
        matches = tag_regex.findall(self.tagged_text, overlapped=True)
        matches = [re.sub('<[\w/-]+?>', '', m) for m in matches]
        return matches


def get_timestamp() -> str:
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def make_extracted_dir(path: str) -> str:
    dir_path = os.path.join(path, EXTRACTED_DIR_BASE + '_' + get_timestamp())
    os.makedirs(dir_path)
    return dir_path


def extract_and_save_tagged_text(files, path, tags):
    ext_dir = make_extracted_dir(path)
    for tag in tags:
        text_for_tag = [[file.file_name] + file.get_text_for_tag(tag) for file in files]
        file_strs = ['\n\n'.join(l) for l in text_for_tag]
        str_to_write = FILE_SEPARATOR.join(file_strs)
        with open(os.path.join(ext_dir, f'{tag}.{TXT_EXT}'), 'w') as f:
            f.write(str_to_write)


def process_directory(path: str) -> None:
    files = get_files(path)
    print('Found files: {}'.format(str([f.file_name for f in files])))
    tags = find_all_tags(files)
    print('Found tags: {}'.format(str(tags)))

    if tags:
        extract_and_save_tagged_text(files, path, tags)
    else:
        print('No tags found.')


def get_files(path: str) -> List[TaggedFile]:
    pattern = os.path.join(path, f'*.{TXT_EXT}')
    txt_file_names = glob.glob(pattern)
    return [TaggedFile(fn) for fn in txt_file_names]


def find_all_tags(files: List[TaggedFile]) -> List[str]:
    tags = set()
    for file in files:
        tags.update(file.list_all_tags())
    tags = list(tags)
    tags.sort()
    return tags


def main():
    print("Tagged file processor")
    parser = argparse.ArgumentParser(description='Extract the tagged text from a folder of files and create new files')
    parser.add_argument('path',
                        help='The directory to process')
    parser.add_argument('--version', '-v', action='store_const', const=True, default=False)
    args = parser.parse_args()

    if args.version:
        with open('version.txt', 'r') as fp:
            version = fp.read()
        print(version)
        return

    print('Processing files from: ' + args.path)

    process_directory(args.path)


if __name__ == '__main__':
    main()
