import requests
import datetime
import json
from tqdm import tqdm

# Вспомогательные функции
# Чтение файла с токенами ВК и Яндекс Облака
with open('tokens.txt') as file_objects:
    TOKEN_VK = file_objects.readline().strip()
    TOKEN_YANDEX = file_objects.readline().strip()

# Функция для поиска фото максимального размера, согласно заданию. Использует метод сортировки
def find_max_image(dict_in_search):
    max_dpi = 0  #Максимальное разрешение
    number_of_element = 0 #Номер элемента для сортировки
    for j in range(len(dict_in_search)):
        file_dpi = dict_in_search[j].get('width') * dict_in_search[j].get('height')
        if file_dpi > max_dpi:
            max_dpi = file_dpi
            number_of_element = j
    return dict_in_search[number_of_element].get('url'), dict_in_search[number_of_element].get('type') #возвращает ссылку и размер фото

# Функция для конвертирования таймстемп в нормальный вид. Вид год-месяц-день час-минута-секунда
def timestamp_to_time(time_unix):
    timestamp = datetime.datetime.fromtimestamp(time_unix)
    time_in_normal_view = timestamp.strftime('%Y-%m-%d time %H-%M-%S')
    return time_in_normal_view

# Класс для выгрузки фото с ВК
class Vk:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}
        self.json, self.export_dict = self._parsed_photo()

    def _get_photo(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id,
                  'album_id': 'profile',
                  'photo_sizes': 1,
                  'extended': 1,
                  'rev': 1
                  }
        photo_info_resp = requests.get(url, params={**self.params, **params})
        if photo_info_resp.status_code == 200: #Проверка статуса ответа на запрос
            print("Запрос в ВКонтакте прошел успешно! Ответ получен")
            photo_info = photo_info_resp.json()['response']
            return photo_info['count'], photo_info['items']
        else:
            print("При запросе  ВКонтакте произошла ошибка. Детальную информацию можно получить из кода ошибки")
            return photo_info_resp.status_code

    def _get_info_about_photo(self):
        photo_count, photo_items = self._get_photo()
        result = {}
        for i in range(photo_count):
            likes_count = photo_items[i]['likes']['count']
            url_download, picture_size = find_max_image(photo_items[i]['sizes'])
            time_warp = timestamp_to_time(photo_items[i]['date'])
            new_value = result.get(likes_count, [])
            new_value.append({'likes_count': likes_count,
                              'add_name': time_warp,
                              'url_picture': url_download,
                              'size': picture_size})
            result[likes_count] = new_value
        return result

    def _parsed_photo(self):
        json_list = [] #Список для JSON-формата
        sorted_dict = {}
        picture_dict = self._get_info_about_photo()
        counter = 0
        for elem in picture_dict.keys():
            for value in picture_dict[elem]:
                if len(picture_dict[elem]) == 1:
                    file_name = f'{value["likes_count"]}.jpeg'
                else:
                    file_name = f'{value["likes_count"]} {value["add_name"]}.jpeg'
                json_list.append({'file name': file_name, 'size': value["size"]})
                if value["likes_count"] == 0:
                    sorted_dict[file_name] = picture_dict[elem][counter]['url_picture']
                    counter += 1
                else:
                    sorted_dict[file_name] = picture_dict[elem][0]['url_picture']
        return json_list, sorted_dict

# Класс для загрузки фото на ЯндексДиск
class Yandex:
    # Инициализация подключения к ЯндексДиску
    def __init__(self, name_of_folder, access_token_YK, count_of_files = 5):
        self.token = access_token_YK
        self.added_files_num = count_of_files
        self.url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        self.headers = {'Authorization': self.token}
        self.folder = self._create_folder(name_of_folder)

    # Создание папки согласно имени, которое передаст пользователь
    def _create_folder(self, name_of_folder):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': name_of_folder}
        if requests.get(url, headers=self.headers, params=params).status_code != 200: # Проверка
            requests.put(url, headers=self.headers, params=params)
            print(f'\n Директория {name_of_folder} создана на Яндекс диске\n')
        else:
            print(f'\n Директория {name_of_folder} уже существует. Будут скопированы файлы с разными именами\n')
        return name_of_folder

    # Получение ссылки для загрузки фото на Яндекс Облако
    def _in_folder(self, name_of_folder):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        params = {'path': name_of_folder}
        resource_resp = requests.get(url, headers=self.headers, params=params)
        if resource_resp.status_code == 200: # Проерка статуса ответа на запрос
            print("Успешно получена ссылка для загрузки фото на Яндекс.Облако! Начинается загрузка...")
            resource = resource_resp.json()['_embedded']['items']
            in_folder_list = []
            for elem in resource:
                in_folder_list.append(elem['name'])
            return in_folder_list
        else:
            print("При получении ссылки для загрузки на Яндекс.Облако произошла ошибка. Детальную информацию можно получить из кода ошибки")
            return resource_resp.status_code

    #Загрузка фотографий на Яндекс Облако
    def _create_copy(self, dict_files):
        files_in_folder = self._in_folder(self.folder)
        copy_counter = 0

        #Использование tqdm как прогресс-бара в консоли
        for key, i in zip(dict_files.keys(), tqdm(range(self.added_files_num))):
            if copy_counter < self.added_files_num:
                if key not in files_in_folder:
                    params = {'path': f'{self.folder}/{key}',
                              'url': dict_files[key],
                              'overwrite': 'false'}
                    requests.post(self.url, headers=self.headers, params=params)
                    copy_counter += 1
                else:
                    print(f'Файл {key} уже существует')
            else:
                break

        print(f'\nЗапрос завершен, новые файлы скопированы: {copy_counter}'
              f'\nВсего файлов в исходном альбоме VK: {len(dict_files)}')


def main():
    #Первая часть задания - выгрузка фото с ВК
    id_vk = input("Введите id пользователя ВК: ") #Ввод ID-пользователя,
    user_vk = Vk(TOKEN_VK, id_vk) #Создание объекта класса UserVk

    #Функции для проверки работоспособости методов
    # print (user_vk._get_photo())
    # print (user_vk._get_info_about_photo())
    # print (user_vk._parsed_photo())

    #Выгрузка JSON-списка в локальный файл
    with open('Info_about_photos_from_VK.json', 'w') as outfile:
        json.dump(user_vk.json, outfile)

    #Вторая часть задания - загрузка фото в Яндекс Облако
    folder_name = input("Введите название папки на Яндекс.Облаке, в которую хотите сохранить фото: ")
    my_yandex = Yandex(folder_name, TOKEN_YANDEX, 5) # Создание объекта класса UserYandex, 5 фото
    my_yandex._create_copy(user_vk.export_dict) # Загрузка в Яндекс Облако


if __name__ == '__main__':
    main()

