import argparse
import glob
import os
from typing import List, Tuple, Set
from YEDDA_Annotator import YeddaFrame
import datetime
import regex as re

half_tag_re = re.compile(r'<(/?)([\w-]+?)>')
TXT_EXT = 'txt'
ANN_EXT = 'ann'
EXTRACTED_DIR_BASE = 'extracted_text'
FILE_SEPARATOR = '''

----------------------------

'''


class TaggedChunk:
    def __init__(self, tags: Set[str]=None, text=None):
        self.tags: Set[str] = tags
        self.text: str = text


class TaggedFile:
    def __init__(self, file_name: str):
        self.file_name: str = file_name
        self.found_tagged: bool = True
        self._untagged_text, self.tagged_text = self._read_files()
        self._all_tags = self._find_all_tags_in_file()
        self._tagged_chunks = self.build_tag_structure(set())

    def _read_files(self) -> Tuple[str, str]:
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
    def all_tags(self):
        return self._all_tags

    @property
    def untagged_text(self) -> str:
        return self._untagged_text

    @property
    def tagged_chunks(self):
        return self._tagged_chunks

    @property
    def annotated_file(self) -> str:
        return f'{self.file_name}.{ANN_EXT}'

    def _find_all_tags_in_file(self) -> Set[str]:
        # print("Finding all tags in " + self.annotated_file)
        matches = YeddaFrame.tag_regex.findall(self.tagged_text, overlapped=True)
        tags = {m[0] for m in matches}
        return tags

    def build_tag_structure(self, input_tags: Set[str], input_chunk=None) -> List[TaggedChunk]:
        if input_chunk is None:
            input_chunk = self.tagged_text

        tagged_chunks: List[TaggedChunk] = []
        for tag in self.all_tags:
            if tag in input_tags:
                continue
            current_tags = input_tags.copy()
            current_tags.add(tag)
            text_chunks = self.get_text_for_tag_from_string(tag, input_chunk, implicit_start_end_tags=True)
            for chunk in text_chunks:
                matches = half_tag_re.findall(chunk)
                if not matches:
                    tagged_chunks.append(TaggedChunk(current_tags, chunk))
                else:
                    tagged_chunks.append(TaggedChunk(current_tags, chunk))
                    tagged_chunks.extend(self.build_tag_structure(current_tags, chunk))
        return tagged_chunks

    def get_text_for_tag(self, tag: str) -> List[str]:
        return self.get_text_for_tag_from_string(tag, self.tagged_text, implicit_start_end_tags=False)

    @staticmethod
    def get_text_for_tag_from_string(tag: str, chunk: str, implicit_start_end_tags: bool=False):
        specific_tag_regex = re.compile('<' + tag + '>(.*?)</' + tag + '>', flags=re.DOTALL)
        matches = specific_tag_regex.findall(chunk, overlapped=True)
        if implicit_start_end_tags:
            half_specific_tag_regex = re.compile('<(/?)(' + tag + ')>', flags=re.DOTALL)
            implicit_matches = half_specific_tag_regex.findall(chunk)
            if implicit_matches:
                pass

        # matches = [half_tag_re.sub('', m) for m in matches]
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
        tags.update(file.all_tags)
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
