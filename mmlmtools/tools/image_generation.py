# Copyright (c) OpenMMLab. All rights reserved.
import random

import torch
from diffusers import (ControlNetModel, StableDiffusionControlNetPipeline,
                       UniPCMultistepScheduler)
from diffusers.pipelines.stable_diffusion import StableDiffusionSafetyChecker
from mmagic.apis import MMagicInferencer
from PIL import Image

from mmlmtools.toolmeta import ToolMeta
from ..utils.file import get_new_image_path
from .base_tool_v1 import BaseToolv1


class Text2ImageTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Generate Image From User Input Text',
        model={'model_name': 'stable_diffusion'},
        description='This is a useful tool '
        'when you want to generate an image from'
        'a user input text and save it to a file. like: generate '
        'an image of an object or something, or generate an image '
        'that includes some objects.',
        input_description='It takes a string as the input, '
        'representing the text that the tool required. ',
        output_description='It returns a string as the output, '
        'representing the image_path. ')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'text',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self._inferencer = None

    def setup(self):
        if self._inferencer is None:
            self.aux_prompt = 'best quality, extremely detailed'
            self._inferencer = MMagicInferencer(
                model_name=self.toolmeta.model['model_name'],
                device=self.device)

    def apply(self, inputs):
        inputs += self.aux_prompt
        if self.remote:
            raise NotImplementedError
        else:
            image_path = get_new_image_path(
                'image/sd-res.png', func_name='generate-image')
            self._inferencer.infer(text=inputs, result_out_dir=image_path)
        return image_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':
            return outputs
        elif self.output_style == 'pil image':  # transformer agent style
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError


class Seg2ImageTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Generate Image Condition On Segmentations',
        model={
            'model_name': 'controlnet',
            'model_setting': 3
        },
        description='This is a useful tool '
        'when you want to generate a new real image from a segmentation image and '  # noqa
        'the user description. like: generate a real image of a '
        'object or something from this segmentation image. or generate a '
        'new real image of a object or something from this segmentation image. ',  # noqa
        input_description='The input to this tool should be a comma separated '
        'string of two, representing the image_path of a segmentation '
        'image and the text description of objects to generate.')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'image_path, text',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self._inferencer = None

    def setup(self):
        if self._inferencer is None:
            self._inferencer = MMagicInferencer(
                model_name=self.toolmeta.model['model_name'],
                model_setting=self.toolmeta.model['model_setting'],
                device=self.device)

    def convert_inputs(self, inputs):
        if self.input_style == 'image_path, text':
            splited_inputs = inputs.split(',')
            image_path = splited_inputs[0]
            text = ','.join(splited_inputs[1:])
        return image_path, text

    def apply(self, inputs):
        image_path, prompt = inputs
        if self.remote:
            raise NotImplementedError
        else:
            out_path = get_new_image_path(
                'image/controlnet-res.png',
                func_name='generate-image-from-seg')
            self._inferencer.infer(
                text=prompt, control=image_path, result_out_dir=out_path)
        return out_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':
            return outputs
        elif self.output_style == 'pil image':  # transformer agent style
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError


class Canny2ImageTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Generate Image Condition On Canny Image',
        model={
            'model_name': 'controlnet',
            'model_setting': 1
        },
        description='This is a useful tool '
        'when you want to generate a new real image from a canny image and '
        'the user description. like: generate a real image of a '
        'object or something from this canny image. or generate a '
        'new real image of a object or something from this edge image. ',
        input_description='The input to this tool should be a comma separated '
        'string of two, representing the image_path of a canny '
        'image and the text description of objects to generate.')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'image_path, text',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self._inferencer = None

    def setup(self):
        if self._inferencer is None:
            self._inferencer = MMagicInferencer(
                model_name=self.toolmeta.model['model_name'],
                model_setting=self.toolmeta.model['model_setting'],
                device=self.device)

    def convert_inputs(self, inputs):
        if self.input_style == 'image_path, text':
            splited_inputs = inputs.split(',')
            image_path = splited_inputs[0]
            text = ','.join(splited_inputs[1:])
        return image_path, text

    def apply(self, inputs):
        image_path, prompt = inputs

        out_path = get_new_image_path(
            'image/controlnet-res.png', func_name='generate-image-from-canny')

        if self.remote:
            from openxlab.model import inference

            out = inference('mmagic/controlnet_canny', [image_path, prompt])

            with open(out_path, 'wb') as file:
                file.write(out)

        else:
            self._inferencer.infer(
                text=prompt, control=image_path, result_out_dir=out_path)
        return out_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':
            return outputs
        elif self.output_style == 'pil image':  # transformer agent style
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError


class Pose2ImageTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Generate Image Condition On Pose Image',
        model={
            'model_name': 'controlnet',
            'model_setting': 2
        },
        description='This is a useful tool '
        'when you want to generate a new real image from a human pose image '
        'and the user description. like: generate a real image of a human '
        'from this human pose image. or generate a new real image of a human '
        'from this pose. ',
        input_description='The input to this tool should be a comma separated '
        'string of two, representing the image_path of a human pose '
        'image and the text description of objects to generate.')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'image_path, text',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self._inferencer = None

    def setup(self):
        if self._inferencer is None:
            self._inferencer = MMagicInferencer(
                model_name=self.toolmeta.model['model_name'],
                model_setting=self.toolmeta.model['model_setting'],
                device=self.device)

    def convert_inputs(self, inputs):
        if self.input_style == 'image_path, text':
            splited_inputs = inputs.split(',')
            image_path = splited_inputs[0]
            text = ','.join(splited_inputs[1:])
        return image_path, text

    def apply(self, inputs):
        image_path, prompt = inputs
        if self.remote:
            raise NotImplementedError
        else:
            out_path = get_new_image_path(
                'image/controlnet-res.png',
                func_name='generate-image-from-pose')
            self._inferencer.infer(
                text=prompt, control=image_path, result_out_dir=out_path)
        return out_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':
            return outputs
        elif self.output_style == 'pil image':  # transformer agent style
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError


class ScribbleText2ImageTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Generate Image Condition On Scribble Image',
        model=None,
        description='This is a useful tool '
        'when you want to generate a new real image from both the user '
        'description and a scribble image or a sketch image. ',
        input_description='The input to this tool should be a comma separated '
        'string of two, representing the image_path of a scribble image '
        'and the text description of objects to generate.')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'image_path, text',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self.torch_dtype = torch.float16 if 'cuda' in device else torch.float32
        self.controlnet = ControlNetModel.from_pretrained(
            'fusing/stable-diffusion-v1-5-controlnet-scribble',
            torch_dtype=self.torch_dtype)
        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            'runwayml/stable-diffusion-v1-5',
            controlnet=self.controlnet,
            safety_checker=StableDiffusionSafetyChecker.from_pretrained(
                'CompVis/stable-diffusion-safety-checker'),
            torch_dtype=self.torch_dtype)
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(
            self.pipe.scheduler.config)
        self.pipe.to(device)
        self.seed = -1
        self.a_prompt = 'best quality, extremely detailed'
        self.n_prompt = 'longbody, lowres, bad anatomy, bad hands, '\
                        ' missing fingers, extra digit, fewer digits, '\
                        'cropped, worst quality, low quality'

    def setup(self):
        pass

    def convert_inputs(self, inputs):
        if self.input_style == 'image_path, text':
            splited_inputs = inputs.split(',')
            image_path = splited_inputs[0]
            text = ','.join(splited_inputs[1:])
        return image_path, text

    def apply(self, inputs):
        image_path, prompt = inputs
        if self.remote:
            raise NotImplementedError
        else:
            image = Image.open(image_path)
            self.seed = random.randint(0, 65535)
            prompt = f'{prompt}, {self.a_prompt}'
            image = self.pipe(
                prompt,
                image,
                num_inference_steps=20,
                eta=0.0,
                negative_prompt=self.n_prompt,
                guidance_scale=9.0).images[0]
            out_path = get_new_image_path(
                image_path, func_name='generate-image-from-scribble')
            image.save(out_path)
        return out_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':
            return outputs
        elif self.output_style == 'pil image':
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError


class DepthText2ImageTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Generate Image Condition On Depth Text',
        model=None,
        description='This is a useful tool '
        'when you want to generate a new real image from both the user '
        'description and a depth image. ',
        input_description='The input to this tool should be a comma separated '
        'string of two, representing the image_path of a scribble image '
        'and the text description of objects to generate.')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'image_path, text',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self.torch_dtype = torch.float16 if 'cuda' in device else torch.float32
        self.controlnet = ControlNetModel.from_pretrained(
            'fusing/stable-diffusion-v1-5-controlnet-depth',
            torch_dtype=self.torch_dtype)
        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            'runwayml/stable-diffusion-v1-5',
            controlnet=self.controlnet,
            safety_checker=StableDiffusionSafetyChecker.from_pretrained(
                'CompVis/stable-diffusion-safety-checker'),
            torch_dtype=self.torch_dtype)

        self.pipe.scheduler = UniPCMultistepScheduler.from_config(
            self.pipe.scheduler.config)
        self.pipe.to(device)
        self.seed = -1
        self.a_prompt = 'best quality, extremely detailed'
        self.n_prompt = 'longbody, lowres, bad anatomy, bad hands, '\
                        ' missing fingers, extra digit, fewer digits, '\
                        'cropped, worst quality, low quality'

    def setup(self):
        pass

    def convert_inputs(self, inputs):
        if self.input_style == 'image_path, text':
            splited_inputs = inputs.split(',')
            image_path = splited_inputs[0]
            text = ','.join(splited_inputs[1:])
        return image_path, text

    def apply(self, inputs):
        image_path, prompt = inputs
        if self.remote:
            raise NotImplementedError
        else:
            image = Image.open(image_path)
            self.seed = random.randint(0, 65535)
            prompt = f'{prompt}, {self.a_prompt}'
            image = self.pipe(
                prompt,
                image,
                num_inference_steps=20,
                eta=0.0,
                negative_prompt=self.n_prompt,
                guidance_scale=9.0).images[0]
            out_path = get_new_image_path(
                image_path, func_name='generate-image-from-depth')
            image.save(out_path)
        return out_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':
            return outputs
        elif self.output_style == 'pil image':
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError