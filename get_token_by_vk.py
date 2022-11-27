import requests


class VK:

    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def users_info(self):
        url = 'https://api.vk.com/method/users.get'
        params = {'user_ids': self.id}
        response = requests.get(url, params={**self.params, **params})
        return response.json()


access_token = 'vk1.a.E3atrFsiqaeBXHETJo6SwS9Mkyb90rERExuOwIPmn-P1rGu2J1Dotw8Jvng2EgEMnQjGzqIRL1NAFbMOGHOi7NFKJOrpSD-bV-B4r31zqQHEm2w_VbIIOa6FaRpAxqcS6niV1BaitiEs_NsHwlXdoDHNAUC2b_ykJpTrNO6wfZ0RPi1SO1lQnIzzESwSXCfTesBGryA0UqVvoTWwgEUyfw'
user_id = '137244087'
vk = VK(access_token, user_id)
print(vk.users_info())
