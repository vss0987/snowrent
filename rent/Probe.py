# def yell(text):
#     """Функция"""
#     return text.upper() + '!'
#
# bark = yell
# print(yell('эй'))
# del yell
# try:
#     print(type(yell))
# except:
#     print('нет такой функции')
#
# print(bark('гав'), bark.__name__, sep='\n')

# func = [bark, str.lower, str.capitalize]
# for f in func:
#     print(f, f('всем привет'))
#
# print(list(map(bark, ['здравствуй', 'эй', 'привет'])))

# def get_speak_func(text, volume):
#     def whisper():
#         return text.lower() + '...'
#     def yell():
#         return text.upper() + '!'
#
#     return yell if volume > 0.5 else whisper
#
# get_speak = get_speak_func('привет', 0.6)
# print(get_speak())


# def make_adder(n):
#     def add(x):
#         return n + x
#     return add
#
# plus_3 = make_adder(3)
# print(plus_3(4))

# class Adder:
#     def __init__(self, n):
#         self.n = n
#
#     def __call__(self, x):
#         return x + self.n
#
#
# pl = Adder(10)
# print(pl(20))

# print((lambda x, y, z: x + y * z)(4, 5, 9))

# print(sorted(range(-5, 6), key=lambda i: i*i))

# def uppercase(func):  # декоратор
#     def wrapper():  # обертка
#         original_res = func()
#         modified_res = original_res.upper()
#         return modified_res
#
#     return wrapper
#
#
# @uppercase
# def greet():
#     return "hello"
#
#
# print(greet())

# def subtract(func):
#     def wrapper(*args):
#         a, b = args
#         return a - b
#     return wrapper
#
# @subtract
# def add(a, b):
#     return a + b
#
#
# print(add(3, 2))

class Solution:
    def count_honestly_even(self, n: int) -> int:
        cnt = 0
        for num in range(1, n):
            if num % 2 == 0:
                cnt += 1
        return cnt


s = Solution()  # Создаем экземпляр класса
print(s.count_honestly_even(10))  # Вызываем метод на экземпляре