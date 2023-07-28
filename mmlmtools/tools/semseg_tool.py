# Copyright (c) OpenMMLab. All rights reserved.

import mmcv
from mmseg.apis import MMSegInferencer

from mmlmtools.toolmeta import ToolMeta
from ..utils.file import get_new_image_path
from .base_tool_v1 import BaseToolv1


class SemSegTool(BaseToolv1):
    DEFAULT_TOOLMETA = dict(
        name='Segment the Image',
        model={'model': 'mask2former_r50_8xb2-90k_cityscapes-512x1024'},
        description='This is a useful tool '
        'when you only want to segment the picture or segment all '
        'objects in the picture. like: segment all objects. ',
        input_description='It takes a string as the input, '
        'representing the image_path. ',
        output_description='It returns a string as the output, '
        'representing the image_path. ')

    def __init__(self,
                 toolmeta: ToolMeta = None,
                 input_style: str = 'image_path',
                 output_style: str = 'image_path',
                 remote: bool = False,
                 device: str = 'cuda'):
        super().__init__(toolmeta, input_style, output_style, remote, device)

        self._inferencer = None

    def setup(self):
        if self._inferencer is None:
            self._inferencer = MMSegInferencer(
                model=self.toolmeta.model['model'], device=self.device)

    def convert_inputs(self, inputs):
        if self.input_style == 'image_path':  # visual chatgpt style
            return inputs
        elif self.input_style == 'pil image':  # transformer agent style
            temp_image_path = get_new_image_path(
                'image/temp.jpg', func_name='temp')
            inputs.save(temp_image_path)
            return temp_image_path
        else:
            raise NotImplementedError

    def apply(self, inputs):
        if self.remote:
            import json

            from openxlab.model import inference

            predict = inference('mmsegmentation/Mask2Former',
                                ['./demo_text_ocr.jpg'])
            print(f'json result:{json.loads(predict)}')
            raise NotImplementedError
        else:
            results = self._inferencer(inputs, return_datasamples=True)
            output_path = get_new_image_path(
                inputs, func_name='semseg-something')
            img = mmcv.imread(inputs)
            img = mmcv.imconvert(img, 'bgr', 'rgb')
            self._inferencer.visualizer.add_datasample(
                'results',
                img,
                data_sample=results,
                draw_gt=False,
                draw_pred=True,
                show=False,
                out_file=output_path)
        return output_path

    def convert_outputs(self, outputs):
        if self.output_style == 'image_path':  # visual chatgpt style
            return outputs
        elif self.output_style == 'pil image':  # transformer agent style
            from PIL import Image
            outputs = Image.open(outputs)
            return outputs
        else:
            raise NotImplementedError