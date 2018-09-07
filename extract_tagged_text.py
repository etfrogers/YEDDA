import argparse
import glob
import os
from enum import Enum
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

    @property
    def clean_text(self) -> str:
        return half_tag_re.sub('', self.text)

    @property
    def label(self):
        return '-'.join(sorted(list(self.tags)))

    @staticmethod
    def label_to_tag_set(label: str) -> Set[str]:
        return set(label.split('-'))


def find_text_with_tag_set(chunks: List[TaggedChunk], tags: Set[str]):
    return sorted([v.clean_text for v in chunks if tags == v.tags])


class TagType(Enum):
    OPEN = 0
    CLOSE = 1


class Tag:
    identifiers = ['', '/']

    def __init__(self, matches: List[str]):
        assert len(matches) == 2
        self.type = TagType(self.identifiers.index(matches[0]))
        self.name = matches[1]

    def get_full_tag(self, tag_type: TagType) -> str:
        return f'<{self.identifiers[tag_type.value]}{self.name}>'


class TaggedFile:
    def __init__(self, file_name: str):
        self.file_name: str = file_name
        self.found_tagged: bool = True
        self._untagged_text, self.tagged_text = self._read_files()
        self._all_tags = self._find_all_tags_in_file()
        self.finished_sets: Set[Tuple[str]] = set()
        self._tagged_chunks: List[TaggedChunk] = self.build_tag_structure([])

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
    def all_tags(self) -> Set[str]:
        return self._all_tags

    @property
    def all_tag_sets(self) -> List[str]:
        return list({c.label for c in self.tagged_chunks})

    @property
    def untagged_text(self) -> str:
        return self._untagged_text

    @property
    def tagged_chunks(self) -> List[TaggedChunk]:
        return self._tagged_chunks

    @property
    def annotated_file(self) -> str:
        return f'{self.file_name}.{ANN_EXT}'

    def _find_all_tags_in_file(self) -> Set[str]:
        # print("Finding all tags in " + self.annotated_file)
        matches = YeddaFrame.tag_regex.findall(self.tagged_text, overlapped=True)
        tags = {m[0] for m in matches}
        return tags

    def build_tag_structure(self, input_tags: List[str], input_chunk=None) -> List[TaggedChunk]:
        if input_chunk is None:
            input_chunk = self.tagged_text

        tagged_chunks: List[TaggedChunk] = []
        for tag in self.all_tags:
            if tag in input_tags:
                continue
            current_tags = input_tags.copy()
            current_tags.append(tag)
            if tuple(current_tags) in self.finished_sets:
                continue
            text_chunks = self.get_text_for_tag_from_string(tag, input_chunk, implicit_start_end_tags=True)
            for chunk in text_chunks:
                matches = half_tag_re.findall(chunk)
                if not matches:
                    tagged_chunks.append(TaggedChunk(set(current_tags), chunk))
                else:
                    tagged_chunks.append(TaggedChunk(set(current_tags), chunk))
                    tagged_chunks.extend(self.build_tag_structure(current_tags, chunk))
            self.finished_sets.add(tuple(current_tags))
        return tagged_chunks

    def get_text_for_tag(self, tag: str) -> List[str]:
        return self.get_text_for_tag_from_string(tag, self.tagged_text, implicit_start_end_tags=False)

    @staticmethod
    def get_text_for_tag_from_string(tag: str, chunk: str, implicit_start_end_tags: bool=False):
        if implicit_start_end_tags:
            half_specific_tag_regex = re.compile('<(/?)(' + tag + ')>', flags=re.DOTALL)
            implicit_matches = half_specific_tag_regex.findall(chunk)
            if implicit_matches:
                # check for first match being closer, and if found add an opening tag at start.
                # vice versa for last match
                first_tag = Tag(implicit_matches[0])
                last_tag = Tag(implicit_matches[-1])
                if first_tag.type == TagType.CLOSE:
                    chunk = first_tag.get_full_tag(TagType.OPEN) + chunk
                if last_tag.type == TagType.OPEN:
                    chunk = chunk + last_tag.get_full_tag(TagType.CLOSE)

        specific_tag_regex = re.compile('<' + tag + '>(.*?)</' + tag + '>', flags=re.DOTALL)
        matches = specific_tag_regex.findall(chunk, overlapped=True)
        return matches


def get_timestamp() -> str:
    return datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def make_extracted_dir(path: str) -> str:
    dir_path = os.path.join(path, EXTRACTED_DIR_BASE + '_' + get_timestamp())
    os.makedirs(dir_path)
    return dir_path


def extract_and_save_tagged_text(files: List[TaggedFile], path: str, tag_labels: List[str]) -> None:
    ext_dir = make_extracted_dir(path)
    for tag_label in tag_labels:
        tag_set = TaggedChunk.label_to_tag_set(tag_label)
        text_list = [[file.file_name] + find_text_with_tag_set(file.tagged_chunks, tag_set) for file in files]
        file_strs = ['\n\n'.join(l) for l in text_list]
        str_to_write = FILE_SEPARATOR.join(file_strs)
        with open(os.path.join(ext_dir, f'{tag_label}.{TXT_EXT}'), 'w') as f:
            f.write(str_to_write)


def process_directory(path: str) -> None:
    files = get_files(path)
    print('Found files: {}'.format(str([f.file_name for f in files])))
    tag_sets = find_all_tag_sets(files)
    print('Found tags: {}'.format(str(tag_sets)))

    if tag_sets:
        extract_and_save_tagged_text(files, path, tag_sets)
    else:
        print('No tags found.')


def get_files(path: str) -> List[TaggedFile]:
    pattern = os.path.join(path, f'*.{TXT_EXT}')
    txt_file_names = glob.glob(pattern)
    return [TaggedFile(fn) for fn in txt_file_names]


def find_all_tag_sets(files: List[TaggedFile]) -> List[str]:
    tags = set()
    for file in files:
        tags.update(file.all_tag_sets)
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
