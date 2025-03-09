import os
from llm_tools import ask_gpt
from dotenv import load_dotenv
from config import (
    MD_FILES_PATH,
    MODEL_REASONING,
    META_INFO_JSON_PATH,
)
from prompt_templates import meta_info_prompt
from response_formats import MetaDocumentInfo
from data_tools import extract_pages
import json
from concurrent.futures import ThreadPoolExecutor
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    # how many pages will be used to get meta data
    NUM_PAGES = 100

    load_dotenv()
    md_files = [file for file in os.listdir(
        MD_FILES_PATH) if file.endswith('.md')]

    def process_file(file):
        file_path = MD_FILES_PATH / file
        context = "\n\n".join(extract_pages(list(range(NUM_PAGES)), file_path))
        prompt = meta_info_prompt.format(num=NUM_PAGES, context=context)
        gpt_response: MetaDocumentInfo = ask_gpt(
            model=MODEL_REASONING,
            prompt=prompt,
            response_format=MetaDocumentInfo,
            reasoning=True,
            timeout=150
        )
        sha1 = os.path.splitext(file)[0]
        return sha1, gpt_response

    with ThreadPoolExecutor(max_workers=30) as executor:
        results = executor.map(process_file, md_files)

    meta_info_dict = {}
    for sha1, meta_info in results:
        meta_info_dict[sha1] = meta_info

    with open(META_INFO_JSON_PATH, "w", encoding="utf-8") as json_file:
        json.dump({sha1: meta_info.model_dump() for sha1, meta_info in meta_info_dict.items()},
                  json_file, ensure_ascii=False, indent=4)
