"""
解密华清的加密内容
"""

import base64
from io import StringIO

import pandas as pd

delta = 2654435769


def join(numbers):
    bytes_array = bytearray()
    for number in numbers:
        bytes_array.extend(number.to_bytes(4, 'little', signed=False))
    return bytes_array


def split(bytes_array):
    numbers = []
    bytes_array_length = len(bytes_array)
    numbers_length = bytes_array_length // 4

    if bytes_array_length % 4 > 0:
        numbers_length += 1
        bytes_array.extend(bytearray(4 - bytes_array_length % 4))

    index = 0
    while index < numbers_length:
        number = int.from_bytes(bytes_array[index * 4:(index + 1) * 4], 'little', signed=False)
        numbers.append(number)
        index += 1

    return numbers


def run(text_bytes, key_bytes):
    text_numbers = split(text_bytes)
    key_numbers = split(key_bytes)
    if len(key_numbers) < 4:
        key_numbers.extend([0] * (4 - len(key_numbers)))

    text_length = len(text_numbers) - 1
    text_first = text_numbers[0]
    rounds = (6 + 52 // (text_length + 1)) * delta & 0xFFFFFFFF

    while rounds != 0:
        q = (rounds >> 2) & 3
        index = text_length

        while index > 0:
            current = text_numbers[index - 1]
            p = ((current >> 5 ^ text_first << 2) + (text_first >> 3 ^ current << 4) ^
                 (rounds ^ text_first) + (key_numbers[index & 3 ^ q] ^ current))
            temp = (text_numbers[index] - p) & 0xFFFFFFFF
            if temp < 0:
                temp += 2 ** 32
            text_first = text_numbers[index] = temp
            index -= 1

        current = text_numbers[text_length]
        p = ((current >> 5 ^ text_first << 2) + (text_first >> 3 ^ current << 4) ^
             (rounds ^ text_first) + (key_numbers[index & 3 ^ q] ^ current))
        temp = (text_numbers[0] - p) & 0xFFFFFFFF
        if temp < 0:
            temp += 2 ** 32

        text_first = text_numbers[0] = temp
        rounds -= delta

        if rounds < 0:
            rounds += 2 ** 32

    return join(text_numbers)


def decode(raw_text):
    suffix = "03a33cd9a31ee58c"
    key = "redwar2021"
    text = raw_text[:-len(suffix)]
    text_bytes = base64.b64decode(text)
    key_bytes = bytearray(key.encode('utf-8'))
    result = run(text_bytes, key_bytes)
    return result.decode('utf-8', errors='replace')


if __name__ == '__main__':
    res = decode(input("输入华清的加密内容（03a33cd9a31ee58c结尾）>>>:\n"))
    res = "\n".join(res.split('\n')[:-1])
    res = pd.read_csv(StringIO(res), sep='\t')
    res.fillna('', inplace=True)
    print(f"解密结果>>>:\n{res}")
