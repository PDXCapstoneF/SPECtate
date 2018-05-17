#!/usr/bin/python3
import json
import uuid
import os
import pathlib
from pathlib import Path
import sys
import copy

# import modules defined at ../
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append('../src/')  # @todo: avoid PYTHONPATH
from src.validate import *
from src.benchmark_run import SpecJBBRun
from src.run_generator import RunGenerator


class RunManager:
    """
    Object used by `mainGUI.py` to structure TemplateData and RunLists in memory,
    allowing some useful operations to isolate run management from the GUI.
    """

    def __init__(self, config_file=None, jar=None):
        self.RUN_CONFIG, self.current_run, self.validated_runs, self.jar = None, None, None, None

        # Find example_config relative to run_manager.py
        self.default_config = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")) \
                                         + '/example_config.json'
        self.template_fields = ["args", "annotations", "prop_options", "types", "translations"]

        # Set paths to config files
        if config_file is None:  # no config file specified, use default that SPECtate provides.
            self.set_config(filepath=self.default_config, config_type="RunList")
        elif config_file is not None:
            self.set_config(filepath=config_file, config_type="RunList")
        if jar is not None:
            self.set_config(filepath=jar, config_type="SPECjbb")

        # load into memory
        self.load_config()

        if not self.initialized():
            print("Run configuration not loaded. Please supply a valid configuration file.")

    def initialized(self):
        """
        Checks that the current runs in memory are not NULL and are set to a correct type.
        A precaution for preventing key errors from arising in other methods.
        :return: Bool
        """
        return True if (self.validated_runs is not None and isinstance(self.validated_runs, dict)) else False

    def set_config(self, filepath, config_type, load=True):
        """
        Sets the configuration filepath for run_list and for SPECjbb jar files.
        Will load new configurations into memory if load=True.
        :param filepath: str
        :param config_type: str
        :param load: bool
        :return:
        """
        extension = pathlib.Path(filepath).suffix
        if "json" in extension and config_type == "RunList":
            if Path(filepath).is_file():  # if given a proper filepath
                self.RUN_CONFIG = filepath
        elif "jar" in extension and config_type == "SPECjbb":
            if Path(filepath).is_file():
                self.jar = filepath
        if load is True:
            self.load_config()

    def load_config(self):
        """
        Loads and validates run configurations, and inserts path to SPECjbb
        jar file into template types so the user can do a run.
        :return:
        """
        if self.RUN_CONFIG is not None:
            if Path(self.RUN_CONFIG).is_file():
                with open(self.RUN_CONFIG) as file:
                    parsed = json.load(file)
                    self.validated_runs = validate(parsed)
        if self.jar is not None:
            if Path(self.jar).is_file():
                for template in self.validated_runs["TemplateData"].keys():  # update each template with this jar's path
                    self.validated_runs["TemplateData"][template]["jar"] = str(self.jar)

    def do_run(self, tag=None, runs_list=None):
        """
        Based on `do_run()` in `mainCLI`, this method also does a run in the root directory.
        Ideally `mainCLI` would be extensible in `mainGUI`, but there are some compatibility issues.
        :return:
        """
        print("Inside do_run")
        with open(self.RUN_CONFIG) as f:
            args = json.loads(f.read())
        rs = RunGenerator(**args)
        os.chdir("..")  # directories made by `SPECjbbRun` will be placed in root.

        if runs_list is not None:  # run list of runs
            for r in rs.runs:
                for i in runs_list:
                    if r["tag"] == i:
                        s = SpecJBBRun(**r)
                        return s.run()

        if tag is not None:  # run specific
            for r in rs.runs:
                if r["tag"] == tag:
                    s = SpecJBBRun(**r)
                    return s.run()

        else:  # run all
            for r in rs.runs:
                s = SpecJBBRun(**r)
                s.run()
        os.chdir("gui/")  # set cwd back to /gui/ when done.

    def write_to_file(self, filepath=None):
        """
        Dumps validated_runs to default or specified file.
        :param filepath:
        :return:
        """
        if filepath:
            with open(filepath, 'w') as fh:
                json.dump(self.validated_runs, fh, indent=4)
        else:
            with open(self.RUN_CONFIG, 'w') as fh:
                json.dump(self.validated_runs, fh, indent=4)

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
        if self.initialized():
            try:
                if key == "TemplateData":
                    self.validated_runs[key][data["RunType"]] = data
                elif key == "RunList":
                    self.validated_runs[key].append(data)
                    return True
            except:  # not a valid run
                return None

    def update_run(self, tag_to_find, data):
        """
        Update a run with new args.
        :param tag_to_find:
        :param data: dict
        :return:
        """
        if not isinstance(tag_to_find, str) or not isinstance(data, dict):
            return None
        for idx, run in enumerate(self.validated_runs["RunList"]):
            if tag_to_find in run["tag"]:  # found run to update
                for key, value in data["args"].items():  # update arg keys
                    run["args"][key] = value
                data.pop("args")
                for key, value in data.items():  # update highest level keys
                    run[key] = value
            return run
        return None

    def create_run(self, run_type):
        """
        Creates a run to insert into run_list. Values will be initialized to a default value.
        :param run_type: str
        :return: str
        """
        if run_type not in self.get_template_types()[0]:
            return None
        run_type_copy = copy.deepcopy(self.validated_runs["TemplateData"][run_type])
        new_args = dict()

        for arg in run_type_copy["args"]:
            if run_type_copy["types"][arg] == "string":
                new_args[arg] = "0"
            if run_type_copy["types"][arg] == "integer":
                new_args[arg] = 0
        run_type_copy["args"] = new_args
        run_type_copy["template_type"] = str(run_type)
        run_type_copy["tag"] = ("{}-{}".format(run_type, str(uuid.uuid4())[:8]))
        self.insert_into_config_list(key="RunList", data=run_type_copy)
        return run_type_copy["tag"]

    def duplicate_run(self, from_tag):
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
            run_copy = copy.deepcopy(run)
            if run_copy is not None and isinstance(run_copy, dict) and "tag" in run_copy:
                run_copy["tag"] = "{}-{}".format(run["tag"], "(copy)")
                # repetitions = run_copy["tag"].count("(copy)")
                if self.insert_into_config_list("RunList", run_copy):
                    return run_copy
                else:
                    return None

    def remove_run(self, tag_to_remove):
        """
        Used to remove run from list. This method is a wrapper for get_run_from_list,
        which passes a delete operation to perform when the run is found.
        :param tag_to_remove:
        :return:
        """
        if self.initialized():
            self.get_run_from_list(tag_to_find=tag_to_remove, action="del")

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
        if self.initialized():
            return self.validated_runs["RunList"]

    def get_run_list_tags(self):
        # @todo: test
        """
        Returns the tags of all runs currently in the run list.
        :return: list
        """
        if self.initialized():
            return [(lambda x: x["tag"])(x) for x in self.get_run_list()]

    def set_current_run(self, new_run_tag):
        # @todo: test
        """
        Sets the current run to track.
        :param new_run_tag:
        :return: string
        """
        self.current_run = new_run_tag
        return self.current_run

    def set_run_index(self, run_tag, to_index):
        """
        Used for reordering runs in RunList.
        :param run_tag: str
        :param to_index: int
        :return: bool
        """
        print("Before: {}".format(self.validated_runs["RunList"]))
        if to_index > len(self.validated_runs["RunList"]) or to_index < 0:
            print("Index out of range.")
            return None
        for idx, item in enumerate(self.validated_runs["RunList"]):
            if item["tag"] == run_tag:
                # old_idx = self.validated_runs["RunList"].index(item)
                self.validated_runs["RunList"][to_index], self.validated_runs["RunList"][idx] = \
                    self.validated_runs["RunList"][idx], self.validated_runs["RunList"][to_index]
                return True
        return False

    def get_current_run(self):
        # @todo: test
        """
        Used to track which run user is currently editing in the MainWindow.
        :return: string
        """
        if self.initialized():
            return self.current_run

    def get_run_from_list(self, tag_to_find, action=None):
        # @todo: test
        """
        Search for run in run list by tag, having the key value `tag_to_find`.
        :param tag_to_find: a string (run tag) to look for
        :param action: str
        :return: dict
        """
        if self.initialized():
            if isinstance(tag_to_find, str):
                for idx, run in enumerate(self.validated_runs["RunList"]):
                    if tag_to_find in run["tag"]:
                        if action == "del":
                            run_copy = copy.deepcopy(run)
                            del self.validated_runs["RunList"][idx]
                            return run_copy
                        return run
        return None

    def get_template_types(self):
        """
        Returns available template types (e.g. ["HBIR", "HBIR_RT", ...]
        :return: list
        """
        if self.initialized():
            return [self.validated_runs["TemplateData"].keys()]

    def get_template_type_args(self, run_type):
        """
        Searches the config file for args pertaining to `run_type`.
        It also returns each arg's annotation, in the form: {'arg_x': 'annotation_x', ...}
        :param run_type: dict or str
        :return: dict
        """
        if self.initialized():
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
                return a["tag"] == b["args"]["Tag"]
            elif isinstance(b, str):
                return a["tag"] == b
        elif isinstance(a, str):
            if isinstance(b, dict):
                return a == b["tag"]
            if isinstance(b, str):
                return a == b


if __name__ == "__main__":
    run_manager = RunManager()
    # new_args = {"tag": "NEW TAG NAME",
    #             "args": {
    #                 "Kit Version": "NEW KIT VERSION"}}
    #
    # run_manager.update_run(tag_to_find="TAG",
    #                        data=new_args)
