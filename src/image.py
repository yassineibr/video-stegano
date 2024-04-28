import abc
from PIL.Image import Image


class AbstractImageStegano(abc.ABC):

    @abc.abstractmethod
    def hide(self, image: str, message: str) -> Image:
        pass

    @abc.abstractmethod
    def unhide(self, image: str) -> str:
        pass
