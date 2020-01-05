
from . import item


class Currency(item.ItemBase):

    influxDB_host = "http://192.168.4.3:8086"
    args = Args()

    def __init__(self, item_dict=None):
        super().__init__(item_dict)
        self.stack_size = item_dict.get('stackSize', None)
        self.value_name = None


    def __str__(self):
        return str(self.__dict__)


    def post_to_influx(self):

        data = ""
        data += f"sale,env={self.args.env},name={self.type_line},value_name={self.value_name} value={self.value},count={self.stack_size}"
        self.log.debug(data)
        return

        host = self.influxDB_host + '/write'
        params = {"db":"poe_currency","precision":"m"}
        try:
            r = requests.post( host, params=params, data=data, timeout=1)
            pass
            # print(data)
        except (KeyboardInterrupt, SystemExit, RuntimeError):
            raise
            return
        except Exception as e:
            self.log.exception("Posting to InfluxDB threw exception")
            # continue