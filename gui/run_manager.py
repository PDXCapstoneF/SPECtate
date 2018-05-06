#!/usr/bin/python3
import json
import uuid
import os
import sys
# import modules defined at ../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../src/')  # @todo: avoid PYTHONPATH
from src.validate import *


class RunManager:
    def __init__(self, config_file=None):
        self.current_run = None
        self.template_fields = ["args", "annotations", "default_props", "types", "translations"]
        self.test_file = "example_test.json"
        if config_file is None:
            self.RUN_CONFIG = os.path.dirname(os.path.abspath('../example_config.json')) + '/example_config.json'
        elif config_file is not None:
            self.RUN_CONFIG = config_file
        try:
            with open(self.RUN_CONFIG) as file:
                parsed = json.load(file)
                self.validated_runs = validate(parsed)
                print(self.validated_runs)
        except IOError:
            print("Error: {} does not exist.\nPlease supply a valid onfiguration file.".format(self.RUN_CONFIG))
        if not self.initialized():
            print("Run configuration not loaded. Please supply a valid configuration file.")

    def initialized(self):
        """
        Checks that the current runs in memory are not NULL and are set to a correct type.
        A precaution for preventing key errors from arising in other methods.
        :return: Bool
        """
        return True if (self.validated_runs is not None and isinstance(self.validated_runs, dict)) else False

    def write_to_file(self):
        test = True
        if test is True:
            with open(self.test_file, 'w') as fh:
                json.dump(self.validated_runs, fh, indent=4)
        else:
            with open(self.RUN_CONFIG, 'w') as fh:
                json.dump(self.validated_runs, fh)

    def insert_into_config_list(self, key, data):
        # @todo: test
        """
        This method can insert a template or run into
        `TemplateData` or `RunList`, respectively.
        :param key: str
        :param data: dict
        :return: dict
        """
        if key not in ["TemplateData", "RunList"] or data is None or not isinstance(data, dict):
            return None
        if self.initialized:
            try:
                if key == "TemplateData":
                    self.validated_runs[key][data["RunType"]] = data
                elif key == "RunList":
                    self.validated_runs["RunList"].append(data)
                    return True
            except Exception:  # not a valid run
                return None

    def create_run(self, run_type):
        """
        # RunList section.

        Creates a run to insert into run_list. Values will be initialized to a default value.
        :param run_type: str
        :return: str
        """
        if run_type not in self.get_template_types()[0]:
            return None
        run_type_copy = self.validated_runs["TemplateData"][run_type].copy()
        new_args = dict()

        for arg in run_type_copy["args"]:
            if run_type_copy["types"][arg] == "string":
                new_args[arg] = "0"
            if run_type_copy["types"][arg] == "integer":
                new_args[arg] = 0
        run_type_copy["args"] = new_args
        run_type_copy["template_type"] = str(run_type)
        run_type_copy["args"]["Tag"] = ("{}-{}".format(run_type, str(uuid.uuid4())[:8]))
        self.insert_into_config_list(key="RunList", data=run_type_copy)
        return run_type_copy["args"]["Tag"]

    def duplicate_run(self, from_tag, new_tag_name):
        # @todo: test
        """
        Insert into run_list a copy of an existing run having the Tag `from_tag`.
        `new_tag_name` will override the tag in the copy.
        :param from_tag: str
        :param new_tag_name: str
        :return:
        """
        if self.initialized():
            run = self.get_run_from_list(from_tag)
            if run is not None and isinstance(run, dict) and "Tag" in run:
                run["Tag"] = new_tag_name
                self.insert_into_config_list("RunList", run)

    def get_template_fields(self):
        """
        Returns fields for the structure of a run template,
        (e.g. `args`, `annotations` `translations`, ...)
        :return: list
        """
        return self.template_fields

    def get_run_list(self):
        """
        Returns runs from run list.
        :return: list
        """
        if self.initialized:
            return self.validated_runs["RunList"]

    def get_run_list_tags(self):
        # @todo: test
        """
        Returns the tags of all runs currently in the run list.
        :return: list
        """
        if self.initialized:
            return [(lambda x: x["args"]["Tag"])(x) for x in self.get_run_list()]

    def set_current_run(self, new_run_tag):
        # @todo: test
        """
        Sets the current run to track.
        :param new_run_tag:
        :return: string
        """
        self.current_run = new_run_tag
        return self.current_run

    def get_current_run(self):
        # @todo: test
        """
        Used to track which run user is currently editing in the MainWindow.
        :return: string
        """
        if self.initialized:
            return self.current_run

    def get_run_from_list(self, tag_to_find):
        # @todo: test
        """
        Search for run in run list by tag, having the key value `tag_to_find`.
        :param tag_to_find: a string (run tag) to look for
        :return: dict
        """
        if self.initialized:
            if isinstance(tag_to_find, str):
                for run in self.get_run_list():
                    if tag_to_find in run["args"]["Tag"]:
                        return run

    def get_template_types(self):
        """
        Returns available template types (e.g. ["HBIR", "HBIR_RT", ...]
        :return: list
        """
        if self.initialized:
            return [self.validated_runs["TemplateData"].keys()]

    def get_template_type_args(self, run_type):
        """
        Searches the config file for args pertaining to `run_type`.
        It also returns each arg's annotation, in the form: {'arg_x': 'annotation_x', ...}
        :param run_type: dict or str
        :return: dict
        """
        if self.initialized:
            if not run_type:
                return None
            if isinstance(run_type, dict):
                run_type = run_type["template_type"]
            if isinstance(run_type, str):
                if run_type not in self.validated_runs["TemplateData"].keys():
                    return None
                results = dict()
                for i in self.validated_runs["TemplateData"][run_type]["args"]:
                    results[i] = self.validated_runs["TemplateData"][run_type]["annotations"][i]
                return results

    def compare_tags(self, a, b):
        """
        Compares run tag `a` with run tag `b`.
        :param a: dict or str
        :param b: dict or str
        :return: Bool
        """
        if a or b is None:
            return False
        if isinstance(a, dict):
            if isinstance(b, dict):
                return a["args"]["Tag"] == b["args"]["Tag"]
            elif isinstance(b, str):
                return a["args"]["Tag"] == b
        elif isinstance(a, str):
            if isinstance(b, dict):
                return a == b["args"]["Tag"]
            if isinstance(b, str):
                return a == b