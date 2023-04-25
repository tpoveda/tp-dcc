#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to work with image sequences inside Photoshop
"""

import os
import tempfile
import shutil
import subprocess

import comtypes.client

from tp.common.psd import document


def load_image_sequence_from_psd(psd_file):
    layers_list = list()
    files_list = list()

    if not os.path.isfile(psd_file):
        return
    ps_app = comtypes.client.CreateObject('Photoshop.Application')
    if not ps_app:
        return
    doc = ps_app.Open(psd_file)
    if not doc:
        return
    options = comtypes.client.CreateObject('Photoshop.PNGSaveOptions')
    for layer in doc.Layers:
        layers_list.extend(document.find_layers(layer))

    export_dir_path = tempfile.mkdtemp()

    try:
        for layer in layers_list:
            layer.Visible = False
    except Exception:
        print('Error while settings layers on file {}'.format(psd_file))
        return list()

    try:
        for i, layer in enumerate(layers_list):
            layer.Visible = True
            layer_name = 'Layer_' + str(i)
            png_file = os.path.join(export_dir_path, layer_name + '.png')
            if os.path.isfile(png_file):
                psd_time = os.state(psd_file)[8]
                png_time = os.stat(png_file)[8]
                if psd_time > png_time:
                    os.remove(png_file)
            if not os.path.exists(png_file):
                doc.SaveAs(png_file, options, True)
            layer.Visible = False
            files_list.append(png_file)
    except Exception as e:
        print('Error exporting layers. Removing temporary folder ...')
        print(e)

        shutil.rmtree(export_dir_path)
        return list()
    subprocess.Popen(r'explorer /select, "' + export_dir_path + '"')
    doc.Close(2)
    if ps_app.Documents.Count <= 0:
        ps_app.Quit()
    return files_list, export_dir_path
