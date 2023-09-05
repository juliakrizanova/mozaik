"""
This module contains tests that run mozaik models and compare their output to a
saved reference.
"""

import numpy as np
import os
from mozaik.storage.queries import *
from mozaik.storage.datastore import PickledDataStore
from mozaik.tools.distribution_parametrization import PyNNDistribution
from parameters import ParameterSet
from .test_models import TestModel

import pytest
import mozaik


class TestLSV1MTinyStepCurrentModule(TestModel):
    """
    Class that runs the a tiny version of the LSV1M model on construction from the mozaik-models
    repository and runs it with MPI. Its testing methods compare the membrane potentials of a
    few neurons and the spike times of all neurons to a saved reference.
    """

    model_run_command = "cd tests/full_model/models/LSV1M_tiny_stepcurrentmodule && python run.py nest 2 param/defaults 'pytest' && cd ../../../.."
    result_path = "tests/full_model/models/LSV1M_tiny_stepcurrentmodule/LSV1M_pytest_____"
    ref_path = "tests/full_model/reference_data/LSV1M_tiny_stepcurrentmodule"

    ds = None  # Model run datastore
    ds_ref = None  # Reference datastore

    @pytest.mark.model
    @pytest.mark.stepcurrentmodule
    @pytest.mark.parametrize(
        "sheet_name", ["X_ON", "X_OFF", "V1_Exc_L4", "V1_Inh_L4", "V1_Exc_L2/3", "V1_Inh_L2/3"]
    )
    def test_spikes(self, sheet_name):
        self.check_spikes(self.ds, self.ds_ref, sheet_name)

    @pytest.mark.model
    @pytest.mark.stepcurrentmodule
    @pytest.mark.parametrize(
        "sheet_name", ["X_ON", "X_OFF", "V1_Exc_L4", "V1_Inh_L4", "V1_Exc_L2/3", "V1_Inh_L2/3"]
    )
    def test_voltages(self, sheet_name):
        self.check_voltages(self.ds, self.ds_ref, sheet_name, max_neurons=25)
