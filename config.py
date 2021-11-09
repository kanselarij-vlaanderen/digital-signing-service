import os

__KANSELARIJ_URL = "http://kanselarij.vo.data.gift/"
SIGNINGHUB_BASE_URI = os.environ.get(
    "SIGNINGHUB_API_URL", __KANSELARIJ_URL).strip("/") + "/"



class __Mode:
    __MODE = os.environ.get("MODE")

    @property
    def dev(self):
        return self.__MODE == "development"

mode = __Mode()
