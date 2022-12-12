import aiohttp
import asyncio
import re

from kikiutils.aes import AesCrypt
from kikiutils.check import isdict
from kikiutils.log import logger
from kikiutils.string import random_str, s2b
from kikiutils.uuid import get_uuid
from random import randint, shuffle
from typing import Union


class DataTransmission:
    def __init__(
        self,
        aes: AesCrypt,
        api_base_url: str = ''
    ):
        self.aes = aes
        self.api_base_url = api_base_url

    async def request(
        self,
        url: str,
        data: dict,
        method: str = 'post',
        data_add_uuid: bool = False,
        **kwargs
    ):
        if not re.match(r'https?:\/\/', url):
            url = f'{self.api_base_url}{url}'

        if data_add_uuid:
            data['uuid'] = get_uuid()

        files = kwargs.pop('files', {})
        formdata = aiohttp.FormData()
        formdata.add_field('hash_file', s2b(self.hash_data(data)))

        for k, v in files.items():
            formdata.add_field(k, v)

        async with aiohttp.request(
            method=method,
            url=url,
            data=formdata,
            **kwargs
        ) as response:
            if self.response_is_text(response):
                return self.process_hash_data(await response.text())

            return await response.content.read()

    def hash_data(self, data: dict):
        for _ in range(1, randint(randint(2, 5), randint(6, 16))):
            data[random_str(randint(8, 16), randint(17, 128))] = random_str(
                randint(8, 32),
                randint(33, 256)
            )

        data_list = list(data.items())
        shuffle(data_list)
        hash_data = self.aes.encrypt(data_list)
        return hash_data

    def process_hash_data(self, hash_text: str) -> dict:
        try:
            return {
                i[0]: i[1]
                for i in self.aes.decrypt(hash_text)
            }
        except:
            pass

    @staticmethod
    def response_is_text(response: aiohttp.ClientResponse):
        for k, v in response.headers.items():
            if k.lower() == 'content-type':
                return 'text/' in v.lower()
        return False


class DataTransmissionSecret:
    data_transmission: DataTransmission

    @classmethod
    async def request(
        cls,
        url: str,
        data: dict = {},
        method: str = 'post',
        data_add_uuid: bool = False,
        wait_success: bool = True,
        log_error: bool = False,
        **kwargs
    ):
        while True:
            try:
                response_data = await cls.data_transmission.request(
                    url,
                    data,
                    method,
                    data_add_uuid,
                    **kwargs
                )
            except Exception as error:
                if log_error:
                    logger.error(f'Request failed：{str(error)}')

                if wait_success:
                    continue

            result = cls.check_response_data(
                response_data,
                wait_success
            )

            if result == 'break':
                return
            elif result:
                return result

            await asyncio.sleep(1)

    @staticmethod
    def check_response_data(
        response_data: Union[bytes, dict],
        wait_success: bool
    ):
        if (
            isdict(response_data)
            and response_data.get('success')
            or not isdict(response_data)
        ):
            return response_data

        if not wait_success:
            return 'break'
