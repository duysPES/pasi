from pysrc.config import Config


class Queuer:
    __queues = dict()

    def add(self, name, queue):
        if not isinstance(queue, Queue):
            raise ValueError(f"{queue} is not of type Queue")

        self.__queues[name] = Queue

    def get(self, name):
        return self.__queues[name]


config = Config()
