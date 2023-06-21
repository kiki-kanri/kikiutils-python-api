import aiohttp
import re

from asyncio import sleep
from kikiutils.aes import AesCrypt
from kikiutils.check import isdict
from kikiutils.decorators import try_and_get_data
from kikiutils.string import s2b
from kikiutils.uuid import get_uuid
from random import shuffle
from typing import Optional


class DataTransmission:
    aes: AesCrypt
    api_base_url: str

    @classmethod
    def hash_data(cls, data: dict):
        data_list = list(data.items())
        shuffle(data_list)
        hash_data = cls.aes.encrypt(data_list)
        return hash_data

    @classmethod
    @try_and_get_data
    def process_hash_data(cls, hash_text: str) -> Optional[dict]:
        return {i[0]: i[1] for i in cls.aes.decrypt(hash_text)}

    @classmethod
    async def request(
        cls,
        url: str,
        data: dict = {},
        method: str = 'post',
        data_add_uuid: bool = False,
        wait_for_success: bool = True,
        **kwargs
    ):
        # Process url and data
        if not re.match(r'https?:\/\/', url):
            url = f'{cls.api_base_url}{url}'

        if data_add_uuid:
            data['uuid'] = get_uuid()

        # Process files
        files = kwargs.pop('files', {})
        formdata = aiohttp.FormData()
        formdata.add_field('hash_file', s2b(cls.hash_data(data)))

        for k, v in files.items():
            formdata.add_field(k, v)

        while True:
            try:
                async with aiohttp.request(
                    method=method,
                    url=url,
                    data=formdata,
                    **kwargs
                ) as response:
                    if response.status > 210:
                        raise ValueError()

                    if 'text/' in response.content_type:
                        result = cls.process_hash_data(await response.text())
                    else:
                        result = await response.content.read()

                    if isdict(result):
                        if not result.get('success') and wait_for_success:
                            raise ValueError()
                    elif result is None and wait_for_success:
                        raise ValueError()

                    return result
            except:
                if not wait_for_success:
                    return
                await sleep(1)
