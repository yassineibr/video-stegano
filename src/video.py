# pylint: disable=import-error,no-name-in-module
import os
import math
import shutil
from subprocess import call, STDOUT
from cv2 import imwrite, VideoCapture
from image import AbstractImageStegano
from PIL import Image
from audio import AbstractAudioStegano


class VideoStegano:

    def __init__(self, image_stegano: AbstractImageStegano, audio_stegano: AbstractAudioStegano):
        self.image_stegano = image_stegano
        self.audio_stegano = audio_stegano
        self.tmp_folder = "./tmp/"
        self.images_path = self.tmp_folder + "images/"
        self.audio_path = self.tmp_folder + "audio.wav"
        self.new_video_path = self.tmp_folder + "video.mov"
        self.new_audio_path = self.tmp_folder + "new_audio.wav"
        self.final_video_path = "final_video.mov"

    def _extract_audio(self, video_path):
        """
        Cette fonction permet d'extraire l'audio de la vidéo qui se trouve à
        video_path et lui attribuer le chemin audio_path
        """
        with open(os.devnull, "w", encoding='utf-8') as devnull:
            call(["ffmpeg", "-i", video_path, "-q:a", "0", "-map",
                  "a", self.audio_path, "-y"], stdout=devnull, stderr=STDOUT)

    def _extract_images(self, video_path):
        """
        Cette fonction permet d'extraire les images de la video qui a le chemin
        video_path et renvoie le nombre des images de vidéo
        """

        # créer le dossier qui va contenir les images de vidéo s'il n'existe pas
        if not os.path.exists(self.images_path):
            os.makedirs(self.images_path)
            print(f"[INFO] Répértoire {self.images_path} est crée")

        vidcap = VideoCapture(video_path)

        # vérifier si la vidéo est ouverte avec succès
        if not vidcap.isOpened():
            print("Erreur lors de l'ouverture de la vidéo.")
            exit()

        count = 0

        while True:
            success, image = vidcap.read()
            if not success:
                break
            imwrite(os.path.join(self.images_path, f"{count}.png"), image)
            count += 1
        # renvoie le nombre des images de la vidéo
        return count

    def _split_string(self, s_str, count):
        """
        cette fonction permet de diviser le texte à cacher dans les images sur
        l'ensemble des images et renvoie une liste qui contient dans chaque
        enploicement la partie du texte à cacher dans une image précise
        """
        # per_c est le nombre de lettres d'on doit cacher dans chaque image
        per_c = math.ceil(len(s_str)/count)
        c_cout = 0
        # dans cette variable on va stocker le texte qui doit être cacher dans l'image courante
        out_str = ''
        # c'est la liste qui contient les texte qu'on doit cacher dans chaque image
        split_list = []
        for s in s_str:
            out_str += s
            c_cout += 1
            # le stockage dans une image est terminé
            if c_cout == per_c:
                split_list.append(out_str)
                out_str = ''
                c_cout = 0
        # dans ce cas la dernière image doit contient moins de lettres que les autres
        if c_cout != 0:
            split_list.append(out_str)
        return split_list

    def _clean_tmp(self):
        """
        cette fonction permet de supprimer le répértoire temporaire qui contient
        un dossier des images de la vidéo et l'audio et la nouvelle vidéo sans
        son
        """
        if os.path.exists(self.tmp_folder):
            shutil.rmtree(self.tmp_folder)
            print("[INFO] le fichier est supprimé avec succès")

    def _hide_images(self, video_path: str, message: str) -> str | None:
        """
        Cette fonction permet de cacher le message dans la video choisie en
        utilisant la méthode hide de la class AbstractImageStegano qui permet de
        cacher un texte dans une image avec un algorithme du choix de
        l'utilisateur
        """

        # count c'est le nombre des images de la vidéo
        count = self._extract_images(video_path)

        split_string_list = self._split_string(message, count)

        for i, elem in enumerate(split_string_list):
            # f_name est le chemin vers la (i+1)ème image
            f_name = f"{self.images_path}{i}.png"
            # avoir la matrice à partir du chemin
            image = Image.open(f_name)
            # image_stegano est une instance de la class AbstractImageStegano et hide est la méthode
            # qui contient le code qui permet de cacher un texte dans une image
            secret_enc = self.image_stegano.hide(image, elem)
            # secret_enc est l'image qui contient le texte caché
            secret_enc.save(f_name)

        return self.final_video_path

    def _unhide_images(self) -> str | None:
        secret = []
        root = self.images_path
        # parcourir les images de la vidéo en utilisant leurs chemins
        for i in range(len(os.listdir(root))):
            f_name = f"{root}{i}.png"
            # Avoir la matrice des pixels de l'image à partir de son chemin
            image = Image.open(f_name)
            try:
                # extraire le texte de l'image en utilisant la méthode unhide de la class ImageStagano
                secret_dec = self.image_stegano.unhide(image)
                if secret_dec is None:
                    break
                # ajouter le texte d'une image dans la liste secret
                secret.append(secret_dec)
            except IndexError:
                break
        # concatener les élémets de la liste pour avoir le message final
        secret = ''.join(secret)
        return secret

    def _hide_audio(self, message: str):
        """
        Cette fonction permet de cacher le message passé en paramètre dans le audio de la vidéo
        """
        self.audio_stegano.hide(self.audio_path, self.new_audio_path, message)

    def _unhide_audio(self) -> str:
        """
        Cette fonction permet de faire sortir le texte caché dans le audio de la vidéo
        """
        return self.audio_stegano.unhide(self.audio_path)


    def hide(self, video_path: str, message: str):
        """
        Cette fonction permet de déviser le message et cacher 75% dans les images et 25% dans le son de la vidéo
        """
        n = (len(message) * 3) // 4
        img_msg = message[:n]
        aud_msg = message[n:]

        # n = len(message)
        # img_msg = "".join([ message[i:i+3] for i in range(0, n, 4)])
        # aud_msg = "".join([ message[i+3:i+4] for i in range(0, n, 4)])

        # self._extract_images(video_path)
        self._hide_images(video_path, img_msg)

        self._extract_audio(video_path)
        self._hide_audio(aud_msg)

        with open(os.devnull, "w", encoding='utf-8') as devnull:
            # fusionner les images dans une video
            call(["ffmpeg", "-i", self.images_path + "%d.png", "-vcodec", "png", self.new_video_path,
                  "-y"], stdout=devnull, stderr=STDOUT)

            # ajouter le son à la nouvelle vidéo
            call(["ffmpeg", "-i", self.new_video_path, "-i", self.new_audio_path, "-codec",
                  "copy", self.final_video_path, "-y"], stdout=devnull, stderr=STDOUT)

        self._clean_tmp()

    def unhide(self, video_path: str) -> str:
        """
        Cette fonction permet d'extraire le texte caché dans les images et le son de la vidéo et les concaténer pour avoir le message final
        """
        self._extract_images(video_path)
        self._extract_audio(video_path)
        img_msg = self._unhide_images()
        aud_msg = self._unhide_audio()

        # msg = "".join([img_msg[3*i:3*i+3] + aud_msg[i:i+1] for i in range(len(aud_msg))])
        # if len(img_msg) % len(aud_msg) != 0:
        #     n = len(aud_msg)
        #     msg += img_msg[3*n:]
        msg = img_msg + aud_msg

        print("Images: " + img_msg + "\nAudio: " + aud_msg)

        self._clean_tmp()
        return msg
