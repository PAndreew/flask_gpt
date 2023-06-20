from __future__ import annotations
import os

from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional

from pydantic import root_validator

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools import BaseTool
from langchain.tools.steamship_image_generation.utils import make_image_public
from langchain.utils import get_from_dict_or_env
from steamship import Steamship
import random
from .models import Notification
from .app import db
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'

def generate_light_color():
    # Generate a random hue
    hue = random.randint(0, 360)
    # Use a fixed saturation and lightness value to achieve a light color
    color = f'hsl({hue}, 70%, 85%)'
    return color

def notify_user(user, message):
    try:
        notification = Notification(user_id=user.id, message=message)
        db.session.add(notification)
        db.session.commit()
    except Exception as e:
        print(f"Failed to notify user {user.id}: {e}")


def upload_to_server(file_content, file_type):
    # Ensuring the upload folder exists
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # Creating a secure filename
    filename = secure_filename(f"{os.urandom(16).hex()}.{file_type}")

    # Saving the file
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Creating a URL to access the file
    file_url = f"/{UPLOAD_FOLDER}/{filename}"
    return file_url


"""This tool allows agents to generate images using Steamship.

Steamship offers access to different third party image generation APIs
using a single API key.

Today the following models are supported:
- Dall-E
- Stable Diffusion

To use this tool, you must first set as environment variables:
    STEAMSHIP_API_KEY
```
"""


if TYPE_CHECKING:
    pass


class ModelName(str, Enum):
    """Supported Image Models for generation."""

    DALL_E = "dall-e"
    STABLE_DIFFUSION = "stable-diffusion"


SUPPORTED_IMAGE_SIZES = {
    ModelName.DALL_E: ("256x256", "512x512", "1024x1024"),
    ModelName.STABLE_DIFFUSION: ("512x512", "768x768"),
}


class SteamshipImageGenerationTool(BaseTool):

    """Tool used to generate images from a text-prompt."""
    model_name: ModelName
    size: Optional[str] = "512x512"
    steamship: Steamship
    return_urls: Optional[bool] = False

    name = "GenerateImage"
    description = (
        "Useful for when you need to generate an image."
        "Input: A detailed text-2-image prompt describing an image"
        "Output: the UUID of a generated image"
    )

    @root_validator(pre=True)
    def validate_size(cls, values: Dict) -> Dict:
        if "size" in values:
            size = values["size"]
            model_name = values["model_name"]
            if size not in SUPPORTED_IMAGE_SIZES[model_name]:
                raise RuntimeError(f"size {size} is not supported by {model_name}")

        return values

    @root_validator(pre=True)
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        steamship_api_key = get_from_dict_or_env(
            values, "steamship_api_key", "STEAMSHIP_API_KEY"
        )

        try:
            from steamship import Steamship
        except ImportError:
            raise ImportError(
                "steamship is not installed. "
                "Please install it with `pip install steamship`"
            )

        steamship = Steamship(
            api_key=steamship_api_key,
        )
        values["steamship"] = steamship
        if "steamship_api_key" in values:
            del values["steamship_api_key"]

        return values

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool."""

        image_generator = self.steamship.use_plugin(
            plugin_handle=self.model_name.value, config={"n": 1, "size": self.size}
        )

        task = image_generator.generate(text=query, append_output_to_file=True)
        task.wait()
        blocks = task.output.blocks
        if len(blocks) > 0:
            if self.return_urls:
                return make_image_public(self.steamship, blocks[0])
            else:
                return blocks[0].id

        raise RuntimeError(f"[{self.name}] Tool unable to generate image!")

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("GenerateImageTool does not support async")