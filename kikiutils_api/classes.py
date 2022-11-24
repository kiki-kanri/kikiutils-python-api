import aiohttp
import asyncio
import re

from kikiutils.aes import AesCrypt
from kikiutils.check import isdict
from kikiutils.string import random_str
from kikiutils.uuid import get_uuid
from random import randint, shuffle

from .utils import response_is_text


class DataTransmission:
    def __init__(
        self,
        key: bytes | str,
        iv: bytes | str,
        api_base_url: str = ''
    ):
        self.api_base_url = api_base_url
        self.iv = iv
        self.key = key
        self.session = aiohttp.ClientSession()

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

        hash_data = self.hash_data(data)

        async with self.session.request(
            method=method,
            url=url,
            data=hash_data,
            **kwargs
        ) as response:
            if response_is_text(response):
                return self.process_hash_data(await response.text())

            return await response.content.read()

    def hash_data(self, data: dict):
        for _ in range(1, randint(randint(2, 5), randint(6, 16))):
            data[random_str(randint(8, 16), randint(17, 128))] = random_str(
                randint(8, 32),
                randint(33, 256)
            )

        data_list = []

        for key, value in data.items():
            data_list.append([key, value])

        shuffle(data_list)
        aes = AesCrypt(self.key, self.iv)
        hash_data = aes.encrypt(data_list)
        return hash_data

    def process_hash_data(self, hash_text: str) -> dict:
        aes = AesCrypt(self.key, self.iv)

        try:
            return {
                i[0]: i[1]
                for i in aes.decrypt(hash_text)
            }
        except:
            pass


class DataTransmissionSecret:
    aes: AesCrypt
    data_transmission: DataTransmission

    @classmethod
    async def request(
        cls,
        url: str,
        data: dict = {},
        method: str = 'post',
        data_add_uuid: bool = False,
        wait_success: bool = True,
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
            except:
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
        response_data: bytes | dict,
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
