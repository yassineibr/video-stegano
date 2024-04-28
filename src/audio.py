import abc


class AbstractAudioStegano(abc.ABC):

    @abc.abstractmethod
    def hide(self, audio_path: str, output_audio: str, message: str):
        pass

    @abc.abstractmethod
    def unhide(self, audio_path: str) -> str:
        pass
